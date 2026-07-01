%% load data
% load("NHL.mat");
% load("leuven_animals.mat");
% load("leuven_animals_exemplar.mat");
% load("leuven_artifacts_category.mat");
% load("leuven_artifacts_exemplar.mat");
% load("animal_frequency_data_matrix.mat");
% load("animal_importance_data_matrix.mat");
% load("animal_random_data_matrix.mat");
% load("artifact_frequency_data_matrix.mat");
% load("artifact_importance_data_matrix.mat");
load("artifact_random_data_matrix.mat");

% M represent input data

%% reordering

% M_reorMder = barycenter(M);
% M_reorder = alternating(M, 10);
% M_reorder = spectral_ordering(M);
% 1) Reorder, but also keep index mapping
[M_reorder, permutace] = barycenter(M);
% [M_reorder, permutace] = alternating(M, 10);
% [M_reorder, permutace] = spectral_ordering(M);
% rowOrder = permutace{1};      % new row i came from original row rowOrder(i)
% colOrder = permutace{2}(:)';  % new col j came from original col colOrder(j)

% Optional sanity check
% assert(isequal(M_reorder, M(rowOrder, colOrder)));


figure;
imshow(~M);
title('Original M');

figure;
imshow(~M_reorder);
title('Reordered M');


%% Otsu method


matrix = M_reorder;
labeledMatrix = zeros(size(matrix)); % Inicializace výstupní matice


% labeledMatrix = deleni(matrix, labeledMatrix, 1, false, 1, 15, 15, 0.60); % run 1
% labeledMatrix = deleni(matrix, labeledMatrix, 1, true,  1, 15, 15, 0.60); % run 2
% labeledMatrix = deleni(matrix, labeledMatrix, 1, true,  1, 15, 20, 0.60); % run 3
% labeledMatrix = deleni(matrix, labeledMatrix, 1, true,  1, 18, 22, 0.55); % run 4
% labeledMatrix = deleni(matrix, labeledMatrix, 1, true,  1, 18, 22, 0.58); % run 5
% labeledMatrix = deleni(matrix, labeledMatrix, 1, true,  1, 10, 10, 0.60); % run 6
% labeledMatrix = deleni(matrix, labeledMatrix, 1, true,  1, 16, 20, 0.55); % run 7
% labeledMatrix = deleni(matrix, labeledMatrix, 1, false, 1, 16, 20, 0.55); % run 8
% labeledMatrix = deleni(matrix, labeledMatrix, 1, true,  1, 16, 20, 0.52); % run 9

% display(labeledMatrix)
[unique_vals, ~, new_labeledMatrix] = unique(labeledMatrix);
labeledMatrix = reshape(new_labeledMatrix, size(labeledMatrix));
% display(labeledMatrix)
figure, tiledlayout(1,2)

nexttile, imshow(matrix);
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


% writematrix(labeledMatrix, 'labeledMatrix.csv') 

rowOrder = permutace{1}(:);   % force column vector
colOrder = permutace{2}(:);   % force column vector

[nr,nc] = size(labeledMatrix);
[rowNew,colNew] = ndgrid(1:nr,1:nc);

label_col    = labeledMatrix(:);
row_new_col  = rowNew(:);
col_new_col  = colNew(:);
row_orig_col = rowOrder(row_new_col);
col_orig_col = colOrder(col_new_col);

% sanity check
N = numel(label_col);
assert(numel(row_new_col)==N && numel(col_new_col)==N && ...
       numel(row_orig_col)==N && numel(col_orig_col)==N);

% mask = (label_col ~= 1);

T = table( ...
    label_col, ...
    row_new_col, ...
    col_new_col, ...
    row_orig_col, ...
    col_orig_col, ...
    'VariableNames', {'label','row_new','col_new','row_orig','col_orig'});

writetable(T, 'label_membership_cells.csv');

% disp(T);

fprintf('Number of unique labels: %d\n', numel(unique(T.label)));
