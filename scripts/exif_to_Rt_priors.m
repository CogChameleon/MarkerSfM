% paths
top = '/hdd/d1/Data/Recon/GeneralPoseSolver/Final';
set = fullfile(top,'statue','weave2');
gravf = fullfile(set,'priors_gravity.txt');
gpsf = fullfile(set,'priors_gps.txt');
exif = fullfile(set,'exif');

%% Read Files

% json exif files
exiffiles = dir(fullfile(exif,'*.exif'));

% for each json file
N = length(exiffiles);
acc = zeros(N,3);
pos = zeros(N,3);
for ii = 1:N

    % decode json
    text = fileread(fullfile(exif,exiffiles(ii).name));
    json = jsondecode(text);
    
    % populate acc and pos
    acc(ii,:) = json.accel';
    pos(ii,:) = [json.gps.latitude, json.gps.longitude, json.gps.altitude];
end


%% Filter

% rotation
sacc = smoothdata(acc);
grav = normr(sacc);
mgrav = mean(grav);
dgrav = median(grav);
sgrav = std(grav);

% position
mpos = mean(pos);
dpos = median(pos);
spos = std(pos);


%% Visualize
%figure;
%plot3(pos(:,1),pos(:,2),pos(:,3),'k.');

% rotation
if 0
    step = 1;
    figure;
    w = 50; wst = 5;
    camh = plot3(pos(1,1), pos(1,3), -pos(1,2), 'r.'); hold on; grid on; axis([-0.1, 0.6, 1.15 1.85, 0.35, 0.95]);
    shah = plot3(pos(1,1), pos(1,3), -pos(1,2), 'k.');
    grah = plot3([pos(1,1) pos(1,1)+grav(1,1)], [pos(1,3) pos(1,3)+grav(1,3)], [-pos(1,2) -pos(1,2)-grav(1,2)], 'r-');
    mgrh = plot3([pos(1,1) pos(1,1)+mgrav(1)], [pos(1,3) pos(1,3)+mgrav(3)], [-pos(1,2) -pos(1,2)-mgrav(2)], 'k-'); 
    plot3(pos(:,1),pos(:,3),-pos(:,2),'k-');
    xlabel('x'); ylabel('y'); zlabel('z');
    pause(0.01);
    for ii = 2:step:length(pos)
        camh.XData = pos(ii,1);
        camh.YData = pos(ii,3);
        camh.ZData = -pos(ii,2);
        fn = max(1,ii-w);
        shah.XData = pos(fn:wst:ii-1,1);
        shah.YData = pos(fn:wst:ii-1,3);
        shah.ZData = -pos(fn:wst:ii-1,2);
        grah.XData = [pos(ii,1) pos(ii,1)+grav(ii,1)];
        grah.YData = [pos(ii,3) pos(ii,3)+grav(ii,3)];
        grah.ZData = [-pos(ii,2) -pos(ii,2)-grav(ii,2)];
        mgrh.XData = [pos(ii,1) pos(ii,1)+mgrav(1)];
        mgrh.YData = [pos(ii,3) pos(ii,3)+mgrav(3)];
        mgrh.ZData = [-pos(ii,2) -pos(ii,2)-mgrav(2)];
        pause(0.01);
    end
end

% position
if 0
    %figure;
    %plot3(pos(:,1),pos(:,2),pos(:,3),'k.'); hold on;
    %plot3(mpos(1),mpos(2),mpos(3),'r*');
    %plot3(dpos(1),dpos(2),dpos(3),'g*');
    
    figure;
    plot(pos(:,1),pos(:,2),'k.'); hold on;
    plot(mpos(1),mpos(2),'r*');
    plot(dpos(1),dpos(2),'g*');
    axis equal;
end



%% Write out Priors

% rotation
rfid = fopen(gravf,'w');
fprintf(rfid,'%f %f %f\n',mgrav(1),mgrav(2),mgrav(3));
fprintf(rfid,'%f %f %f\n',dgrav(1),dgrav(2),dgrav(3));
fprintf(rfid,'%f %f %f',sgrav(1),sgrav(2),sgrav(3));

% position
pfid = fopen(gpsf,'w');
fprintf(pfid,'%f %f %f\n',mpos(1),mpos(2),mpos(3));
fprintf(pfid,'%f %f %f\n',dpos(1),dpos(2),dpos(3));
fprintf(pfid,'%f %f %f',spos(1),spos(2),spos(3));

% close
fclose(rfid);
fclose(pfid);