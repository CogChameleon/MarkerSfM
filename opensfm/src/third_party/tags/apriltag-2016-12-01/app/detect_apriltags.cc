
//system
#include <stdio.h>
#include <iostream>
#include <string>
#include <libgen.h>
#include <dirent.h>
#include <algorithm>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <vector>

//opencv
#include "opencv2/opencv.hpp"

//boost
#include <boost/property_tree/ptree.hpp>
#include <boost/property_tree/json_parser.hpp>
#include <boost/filesystem.hpp>

//apriltag
#include "apriltag.h"
#include "tag36h11.h"
#include "tag36h10.h"
#include "tag36artoolkit.h"
#include "tag25h9.h"
#include "tag25h7.h"
#include "common/getopt.h"

//namespaces
using namespace std;
using namespace cv;


/*===========================================================*/
/*========================= Helpers =========================*/
/*===========================================================*/

/*--------------- Write Detections ---------------*/
void writeDetections(string jsonfile, string imagename, zarray_t *detections, Mat &frame)
{
    //proprety tree to hold json
    boost::property_tree::ptree item_root;
    boost::property_tree::ptree detections_node;

    //if file exists, try to read it
    if ( boost::filesystem::exists( jsonfile ) )
    {
        // try to open it as json
        try
        {
            boost::property_tree::read_json(jsonfile,item_root);
            detections_node = item_root.get_child("detections");
        }
        //error caught, could be that file isn't json?
        catch (...)
        {
            cout << "detect_apriltags.cc :: writeDetections : could not open json file "+jsonfile << endl;
            return;
        }
    }

    // now add the new attribute to the tree
    try
    {
        // image_node
        boost::property_tree::ptree image_node;
        image_node.put("num_dets",zarray_size(detections));

        // for each detection
        boost::property_tree::ptree dets_node;
        for(int i = 0; i < zarray_size(detections); i++)
        {
            // get detection
            apriltag_detection_t *det;
            zarray_get(detections, i, &det);

            // detection node
            boost::property_tree::ptree detection_node;

            // hamming (int hamming)
            detection_node.put("hamming",det->hamming);

            // goodness (float goodness)
            detection_node.put("goodness",det->goodness);

            // decision margin (float decision_margin)
            detection_node.put("margin",det->decision_margin);

            // homography (matd_t *H)
            boost::property_tree::ptree homography_node;
            for(int r = 0; r < det->H->nrows; r++)
            {
                boost::property_tree::ptree row;
                for(int c = 0; c < det->H->ncols; c++)
                {
                    boost::property_tree::ptree cell;
                    cell.put_value( matd_get(det->H, r, c) );
                    row.push_back( make_pair("",cell) );
                }
                homography_node.push_back( make_pair("",row) );
            }
            detection_node.put_child("homography",homography_node);

            // center (double c[2])
            boost::property_tree::ptree cx_node, cy_node;
            cx_node.put("", det->c[0]);
            cy_node.put("", det->c[1]);
            boost::property_tree::ptree center_node;
            center_node.push_back( make_pair("",cx_node) );
            center_node.push_back( make_pair("",cy_node) );
            detection_node.put_child("center",center_node);

            // corners (counter-clockwise) (double p[4][2])
            boost::property_tree::ptree corners_node;
            for(int r = 0; r < 4; r++)
            {
                boost::property_tree::ptree row;
                for(int c = 0; c < 2; c++)
                {
                    boost::property_tree::ptree cell;
                    cell.put_value(det->p[r][c]);
                    row.push_back( make_pair("",cell) );
                }
                corners_node.push_back( make_pair("",row) );
            }
            detection_node.put_child("corners",corners_node);

            // colors (for each corner x RGB) (int p[4][3])
            boost::property_tree::ptree colors_node;
            for(int r = 0; r < 4; r++)
            {
                //get color from frame
                double u = det->p[r][0];
                double v = det->p[r][1];
                Vec3b color(255,255,255);
                if(u >= 0 && v >= 0 && u < frame.cols && v < frame.rows ) //tag corner inside image
                {
                    Vec3b color = frame.at<Vec3b>( Point(u,v) );
                }
                

                boost::property_tree::ptree row;
                for(int c = 0; c < 3; c++)
                {
                    boost::property_tree::ptree cell;
                    cell.put_value( color.val[c] );
                    row.push_back( make_pair("",cell) );
                }
                colors_node.push_back( make_pair("",row) );
            }
            detection_node.put_child("colors",colors_node);

            // add detection
            string id = to_string(det->id);
            dets_node.push_back( make_pair(id,detection_node) );
        }

        // add detections to image
        image_node.put_child("dets",dets_node);

        // add image to detections
        boost::filesystem::path p(imagename);
        detections_node.add_child( boost::property_tree::ptree::path_type(p.filename().string(), '|'), image_node);

        // add detections to root
        item_root.put_child("detections",detections_node);
    }
    catch (...)
    {
        cout << "detect_apriltags.cc :: writeDetections : could not add key value pair." << endl;
        return;
    }

    // output to json
    try
    {
        // write new json to stringstream, the false turns off pretty print
        stringstream ss;
        boost::property_tree::write_json(ss, item_root, true);
        
        // write stringstream to file
        ofstream os;
        os.open(jsonfile.c_str());
        os << ss.str();
        os.close();
    }
    catch (...)
    {
        cout << "detect_apriltags.cc :: writeDetections : could not write to file " << jsonfile << endl;
        return;
    }
}
/*------------- End Write Detections -------------*/

/*--------------- Draw Detections ---------------*/
void drawDetections(zarray_t *detections, Mat &frame)
{
    // Draw detection outlines
    for (int i = 0; i < zarray_size(detections); i++) 
    {
        apriltag_detection_t *det;
        zarray_get(detections, i, &det);
        line(frame, Point(det->p[0][0], det->p[0][1]), Point(det->p[1][0], det->p[1][1]), Scalar(0, 0xff, 0), 3);
        line(frame, Point(det->p[0][0], det->p[0][1]), Point(det->p[3][0], det->p[3][1]), Scalar(0, 0, 0xff), 3);
        line(frame, Point(det->p[1][0], det->p[1][1]), Point(det->p[2][0], det->p[2][1]), Scalar(0xff, 0, 0), 3);
        line(frame, Point(det->p[2][0], det->p[2][1]), Point(det->p[3][0], det->p[3][1]), Scalar(0xff, 0, 0), 3);

        stringstream ss;
        ss << det->id;
        String text = ss.str();
        int fontface = FONT_HERSHEY_SCRIPT_SIMPLEX;
        double fontscale = 1.0;
        int baseline;
        Size textsize = getTextSize(text, fontface, fontscale, 2, &baseline);
        putText(frame, text, Point(det->c[0]-textsize.width/2, det->c[1]+textsize.height/2), fontface, fontscale, Scalar(0xff, 0x99, 0), 2);
    }
}
/*------------- End Draw Detections -------------*/

/*--------------- Files In Folder ---------------*/
void filesInFolder(string folder_param, vector<string> &fileList)
{
	//open directory
    DIR *dir;
    struct dirent *ent;
	dir = opendir(folder_param.c_str());

	//directory found
    if (dir != NULL) 
	{
		//iterate over all files in directory
        while ((ent = readdir (dir)) != NULL) 
		{
			//get file name
            string imgName = ent->d_name;
			string imgPath = folder_param + '/' + imgName;

			//push back
			fileList.push_back( imgPath );
        }

		//close directory
        closedir(dir);
    } 
	else { cout << "detect_apriltags.cc :: " << "Process_Folder : " << "Could not open: "+folder_param << endl; }

	//sort image list by timestamp
	sort(fileList.begin(), fileList.end());
}
/*------------- End Files In Folder -------------*/

/*===========================================================*/
/*========================= Helpers =========================*/
/*===========================================================*/





/*========================================================*/
/*========================= Main =========================*/
/*========================================================*/
int main(int argc, char *argv[])
{
    /*--------------- Input Options ---------------*/
    getopt_t *getopt = getopt_create();

    getopt_add_bool(getopt, 'h', "help", 0, "Show this help");
    getopt_add_bool(getopt, 'd', "debug", 0, "Enable debugging output (slow)");
    getopt_add_bool(getopt, 'q', "quiet", 0, "Reduce output");
    getopt_add_bool(getopt, 's', "show", 0, "for -F, displays window with detections");
    getopt_add_string(getopt, 'f', "family", "tag36h11", "Tag family to use");
    getopt_add_string(getopt, 'F', "input_folder", "", "Process folder of images");
    getopt_add_string(getopt, 'i', "input_file", "", "Process image file");
    getopt_add_string(getopt, 'J', "json_output", "", "Write detections to json");
    getopt_add_int(getopt, 'r', "resize", "0", "Max width for resizing images before processing");
    getopt_add_int(getopt, '\0', "border", "1", "Set tag family border size");
    getopt_add_int(getopt, 't', "threads", "4", "Use this many CPU threads");
    getopt_add_double(getopt, 'x', "decimate", "1.0", "Decimate input image by this factor");
    getopt_add_double(getopt, 'b', "blur", "0.0", "Apply low-pass blur to input");
    getopt_add_bool(getopt, '0', "refine-edges", 1, "Spend more time trying to align edges of tags");
    getopt_add_bool(getopt, '1', "refine-decode", 0, "Spend more time trying to decode tags");
    getopt_add_bool(getopt, '2', "refine-pose", 0, "Spend more time trying to precisely localize tags");

    if (!getopt_parse(getopt, argc, argv, 1) || getopt_get_bool(getopt, "help")) 
    {
        printf("Usage: %s [options]\n", argv[0]);
        getopt_do_usage(getopt);
        exit(0);
    }

    /*------------- End Input Options -------------*/

    

    /*--------------- Setup ---------------*/

    // tag family setup
    apriltag_family_t *tf = NULL;
    const char *famname = getopt_get_string(getopt, "family");
    if (!strcmp(famname, "tag36h11"))
        tf = tag36h11_create();
    else if (!strcmp(famname, "tag36h10"))
        tf = tag36h10_create();
    else if (!strcmp(famname, "tag36artoolkit"))
        tf = tag36artoolkit_create();
    else if (!strcmp(famname, "tag25h9"))
        tf = tag25h9_create();
    else if (!strcmp(famname, "tag25h7"))
        tf = tag25h7_create();
    else {
        printf("Unrecognized tag family name. Use e.g. \"tag36h11\".\n");
        exit(-1);
    }
    tf->black_border = getopt_get_int(getopt, "border");

    // tag detector setup
    apriltag_detector_t *td = apriltag_detector_create();
    apriltag_detector_add_family(td, tf);
    td->quad_decimate = getopt_get_double(getopt, "decimate");
    td->quad_sigma = getopt_get_double(getopt, "blur");
    td->nthreads = getopt_get_int(getopt, "threads");
    td->debug = getopt_get_bool(getopt, "debug");
    td->refine_edges = getopt_get_bool(getopt, "refine-edges");
    td->refine_decode = getopt_get_bool(getopt, "refine-decode");
    td->refine_pose = getopt_get_bool(getopt, "refine-pose");
    
    // mode
    int mode = 0;
    bool show_detections = show_detections = getopt_get_bool(getopt, "show");
    bool write_detections = false;
    const char *input_folder = getopt_get_string(getopt, "input_folder");
    const char *input_file = getopt_get_string(getopt, "input_file");
    const char *json_output = getopt_get_string(getopt, "json_output");
    if( strcmp(input_folder,"") )
    {
        mode = 1;
    }
    else if( strcmp(input_file,"") )
    {
        mode = 2;
    }
    if( (mode == 1 || mode == 2) && strcmp(json_output,"") )
    {
        write_detections = true;
    }

    // resize
    bool should_resize = false;
    int maxWd = getopt_get_int(getopt, "resize");
    if(maxWd > 0) { should_resize = true; }

    /*------------- End Setup -------------*/



    /*--------------- From Folder ---------------*/
    if(mode == 1)
    {
        cout << "Tag Detection from Folder: " << input_folder << endl;

        // get files in folder (assume they are images)
        vector<string> imageList;
        filesInFolder( string(input_folder), imageList);
        cout << "    " << imageList.size() << " images found." << endl;

        // image container
        Mat frame, gray;

        for(vector<string>::iterator it = imageList.begin(); it != imageList.end(); ++it)
        {
            //read image
            frame = cv::imread(*it);
        
            //read okay?
            if(!frame.data) { cout << "detect_apriltag.cc :: " << "main : " << "Could not open: "+(*it) << endl; }
            else
            {
                // resize
                if(should_resize && frame.cols > maxWd)
                {
                    int maxHt = maxWd * frame.rows / frame.cols;
                    double htF = static_cast<double>(maxWd) / frame.cols;
                    double wdF = static_cast<double>(maxHt) / frame.rows;
                    resize(frame,frame, Size(), wdF, htF, cv::INTER_CUBIC);
                }

                // create image_u8
                cvtColor(frame, gray, COLOR_BGR2GRAY);
                image_u8_t im = { .width = gray.cols, .height = gray.rows, .stride = gray.cols, .buf = gray.data };

                // detect
                zarray_t *detections = apriltag_detector_detect(td, &im);
                cout << "    Detected " << zarray_size(detections) << " tags in " << *it << endl;

                // write
                if(write_detections)
                {
                    writeDetections(string(json_output), *it, detections, frame);
                }

                // show
                if(show_detections)
                {
                    drawDetections(detections, frame);
                    imshow("Tag Detections", frame);
                    waitKey(1);
                }

                // destroy
                zarray_destroy(detections);
            }
        }
    }
    /*------------- End From Folder -------------*/

    /*--------------- From File ---------------*/
    else if(mode == 2)
    {
        cout << "Tag Detection from File: " << input_file << endl;

        // image container
        Mat frame, gray;

        //read image
        std::string input_file_str(input_file);
        frame = cv::imread(input_file_str);
    
        //read okay?
        if(!frame.data) { cout << "detect_apriltag.cc :: " << "main : " << "Could not open: "+input_file_str << endl; }
        else
        {
            // resize
            if(should_resize && frame.cols > maxWd)
            {
                int maxHt = maxWd * frame.rows / frame.cols;
                double htF = static_cast<double>(maxWd) / frame.cols;
                double wdF = static_cast<double>(maxHt) / frame.rows;
                resize(frame,frame, Size(), wdF, htF, cv::INTER_CUBIC);
            }

            // create image_u8
            cvtColor(frame, gray, COLOR_BGR2GRAY);
            image_u8_t im = { .width = gray.cols, .height = gray.rows, .stride = gray.cols, .buf = gray.data };

            // detect
            zarray_t *detections = apriltag_detector_detect(td, &im);
            cout << "    Detected " << zarray_size(detections) << " tags in " << input_file_str << endl;

            // write
            if(write_detections)
            {
                writeDetections(string(json_output), input_file_str, detections, frame);
            }

            // show
            if(show_detections)
            {
                drawDetections(detections, frame);
                imshow("Tag Detections", frame);
                waitKey(1);
            }

            // destroy
            zarray_destroy(detections);
        }
        
    }
    /*------------- End From File -------------*/

    /*--------------- From Camera ---------------*/
    else
    {
        // image container 
        Mat frame, gray;
        
        // Initialize camera
        VideoCapture cap(0);
        if (!cap.isOpened()) {
            cerr << "Couldn't open video capture device" << endl;
            return -1;
        }

        // go
        while (true) 
        {
            // get frame
            cap >> frame;
            cvtColor(frame, gray, COLOR_BGR2GRAY);

            // Make an image_u8_t header for the Mat data
            image_u8_t im = { .width = gray.cols,
                .height = gray.rows,
                .stride = gray.cols,
                .buf = gray.data
            };

            // detect
            zarray_t *detections = apriltag_detector_detect(td, &im);
            cout << zarray_size(detections) << " tags detected" << endl;

            // Draw detection outlines
            for (int i = 0; i < zarray_size(detections); i++) 
            {
                apriltag_detection_t *det;
                zarray_get(detections, i, &det);
                line(frame, Point(det->p[0][0], det->p[0][1]), Point(det->p[1][0], det->p[1][1]), Scalar(0, 0xff, 0), 2);
                line(frame, Point(det->p[0][0], det->p[0][1]), Point(det->p[3][0], det->p[3][1]), Scalar(0, 0, 0xff), 2);
                line(frame, Point(det->p[1][0], det->p[1][1]), Point(det->p[2][0], det->p[2][1]), Scalar(0xff, 0, 0), 2);
                line(frame, Point(det->p[2][0], det->p[2][1]), Point(det->p[3][0], det->p[3][1]), Scalar(0xff, 0, 0), 2);

                stringstream ss;
                ss << det->id;
                String text = ss.str();
                int fontface = FONT_HERSHEY_SCRIPT_SIMPLEX;
                double fontscale = 1.0;
                int baseline;
                Size textsize = getTextSize(text, fontface, fontscale, 2, &baseline);
                putText(frame, text, Point(det->c[0]-textsize.width/2, det->c[1]+textsize.height/2), fontface, fontscale, Scalar(0xff, 0x99, 0), 2);
            }
            zarray_destroy(detections);

            imshow("Tag Detections", frame);
            if (waitKey(30) >= 0)
                break;
        }

    }
    /*------------- End From Camera -------------*/



    /*--------------- Shutdown ---------------*/

    // destroy
    apriltag_detector_destroy(td);
    if (!strcmp(famname, "tag36h11"))
        tag36h11_destroy(tf);
    else if (!strcmp(famname, "tag36h10"))
        tag36h10_destroy(tf);
    else if (!strcmp(famname, "tag36artoolkit"))
        tag36artoolkit_destroy(tf);
    else if (!strcmp(famname, "tag25h9"))
        tag25h9_destroy(tf);
    else if (!strcmp(famname, "tag25h7"))
        tag25h7_destroy(tf);
    getopt_destroy(getopt);

    // return
    return 0;

    /*------------- End Shutdown -------------*/
}
/*========================================================*/
/*========================= Main =========================*/
/*========================================================*/