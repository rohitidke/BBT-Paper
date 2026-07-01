% T = readtable('animal_exemplar_feature_matrix_dichotomized.csv');
% M = table2array(T(:,2:end));
% save(['leuven_animals_exemplar.mat'],'M')

% T = readtable('artifact_category_feature_matrix_dichotomized.csv');
% M = table2array(T(:,2:end));
% save(['leuven_artifacts_category.mat'],'M')

% T = readtable('artifact_exemplar_feature_matrix_dichotomized.csv');
% M = table2array(T(:,2:end));
% save(['leuven_artifacts_exemplar.mat'],'M')

% T = readtable('animal_frequency_data_matrix.csv');
% M = table2array(T(:,2:end));
% save(['animal_frequency_data_matrix.mat'],'M')

% T = readtable('animal_importance_data_matrix.csv');
% M = table2array(T(:,2:end));
% save(['animal_importance_data_matrix.mat'],'M')

% T = readtable('animal_random_data_matrix.csv');
% M = table2array(T(:,2:end));
% save(['animal_random_data_matrix.mat'],'M')

% T = readtable('artifact_frequency_data_matrix.csv');
% M = table2array(T(:,2:end));
% save(['artifact_frequency_data_matrix.mat'],'M')

% T = readtable('artifact_importance_data_matrix.csv');
% M = table2array(T(:,2:end));
% save(['artifact_importance_data_matrix.mat'],'M')

T = readtable('artifact_random_data_matrix.csv');
M = table2array(T(:,2:end));
save(['artifact_random_data_matrix.mat'],'M')