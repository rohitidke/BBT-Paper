%% load data
% load("NHL.mat");
load("leuven_animals.mat");

% M represent input data

%% reordering

M_reorder = barycenter(M)';
% M_reorder = alternating(M, 10);
% M_reorder = spectral_ordering(M);

figure;
imshow(~M);
title('Original M');

figure;
imshow(~M_reorder);
title('Reordered M');

[r, c] = size(M_reorder);

max_dim = max(r, c);

% next power of 2
target_dim = 2^nextpow2(max_dim);

M_padded = zeros(target_dim, target_dim);
M_padded(1:r, 1:c) = M_reorder;

M_reorder = M_padded;

figure;
imshow(~M_reorder);
title('Reordered padded M');

%% apply quadtree

% basic setting
box_sizes = [2048 1024 512 256 128 64 32 16 8 4 2 1];
threshold = 0.99;
mindim = 16;

N = M_reorder;
S = qtdecomp(N, threshold, mindim);

blocks = repmat(uint8(0), size(S));

for dim = box_sizes
    numblocks = length(find(S==dim));
    if (numblocks > 0)
        values = repmat(uint8(1),[dim dim numblocks]);
        values(2:dim, 2:dim,:) = 0;
        blocks = qtsetblk(blocks, S, dim, values);
    end
end

%% show results
f = figure;

% original data
imshow(~M_reorder);

% bounding boxes
hold on
for dim = box_sizes
    [x, y] = find(S == dim);
    for i = 1:length(x)
        rectangle('Position', [y(i)-0.5, x(i)-0.5, dim, dim], ...
            'EdgeColor', 'r', 'LineWidth', 1);
    end
end
hold off

f.Color = [0.9, 0.9, 0.9];



%% apply SLIC

pocet_box = 0;

img = double(M_reorder);
numSuperpixels = 16; % no of superpixels
[L, N] = superpixels(img, numSuperpixels);

% replace points by superpixesl
outputImg = zeros(size(img));
for k = 1:N
    mask = (L == k);
    meanColor = median(img(mask)); % average value for each superpixel
    if(meanColor == 1)
        pocet_box = pocet_box + 1;
    end
    outputImg(mask) = meanColor;
end

P = outputImg;
figure;
imshow(label2rgb(L));
title('SLIC Regions');


num_cluster = max(L(:));
boxy = [];
figure,
imshow(P,[]);
hold on;
for k = 1 : num_cluster
    mask = (L == k);
    meanColor = median(M_reorder(mask)); % avg. value
    if(meanColor == 1)
        [b_x, b_y] = find(mask);
        prvni_x = min(b_x);
        posledni_x = max(b_x);
        prvni_y = min(b_y);
        posledni_y = max(b_y);
        velikost_x = posledni_x - prvni_x+1;
        velikost_y = posledni_y - prvni_y+1;
    end
    outputImg(mask) = meanColor;

end
hold off;

figure, imshow(P);

img = double(M_reorder);
[y, x] = find(img); % find white points 
data = [x, y]; % vectorization

% settings
epsilon = 2; % maximal distace between points in cluster
minPts = 5; % minimal numbuer of points in cluster
clustIdx = dbscan(data, epsilon, minPts);

% new picture 
K = false(size(img));
for k = 1:max(clustIdx)
    clusterPoints = data(clustIdx == k, :);
    for i = 1:size(clusterPoints, 1)
        K(clusterPoints(i,2), clusterPoints(i,1)) = true;
    end
end

% figure,
% subplot(1,2,1), imshow(imresize(1-M_reorder,10,"nearest"), []);

%% plot reults
subplot(1,2,2), imshow(1-K, []); % 
hold on
numClusters = max(clustIdx);
for k = 1:numClusters
    clusterPoints = data(clustIdx == k, :); % 

    if isempty(clusterPoints)
        continue;
    end

    % bouding box
    minX = min(clusterPoints(:,1));
    maxX = max(clusterPoints(:,1));
    minY = min(clusterPoints(:,2));
    maxY = max(clusterPoints(:,2));

    % plot box
    rectangle('Position', [minX, minY, maxX-minX, maxY-minY], ...
        'EdgeColor', 'r', 'LineWidth', 2);
end
hold off


