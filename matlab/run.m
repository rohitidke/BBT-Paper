%% load data
load("NHL.mat");
% load("leuven_animals.mat");

% M represent input data

%% reordering

M_reorder = barycenter(M);
% M_reorder = alternating(M, 10);
% M_reorder = spectral_ordering(M);

figure;
imshow(~M);
title('Original M');

figure;
imshow(~M_reorder);
title('Reordered M');


%% Otsu method


matrix = M_reorder;
labeledMatrix = zeros(size(matrix)); % Inicializace výstupní matice

labeledMatrix = deleni(matrix, labeledMatrix, 1, true, 1, 3,3, 0.8);

% display(labeledMatrix);
[unique_vals, ~, new_labeledMatrix] = unique(labeledMatrix);
labeledMatrix = reshape(new_labeledMatrix, size(labeledMatrix));

figure, tiledlayout(1,2)

nexttile, imshow(~matrix);
nexttile, imshow(labeledMatrix, []);


figure,
imshow(~M_reorder,[]);

hold on
for dim = unique(labeledMatrix)'
    if(dim == 1)
        continue;
    end
    [x, y] = find(labeledMatrix == dim, 1,"first");
    [x2, y2] = find(labeledMatrix == dim, 1,"last");
    rectangle('Position', [y-0.5, x-0.5, y2-y+1, x2-x+1], ...
        'EdgeColor', 'r', 'LineWidth', 1);
end
hold off
