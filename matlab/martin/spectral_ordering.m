function [C, permutace] = spectral_ordering(M)
%SPECTRAL_ORDERING implements spectral ordering + bidirectional fixed permutation (Algorithm 2)

[m,n] = size(M);
S = zeros(n,n);

% % % % % Marketa
permutace_x = (1 : size(M,1));
permutace_y = (1 : size(M,2))';
% % % % %


% first we compute a similarity matrix S via (symetric) similarity measure
for i=1:n
    for j=i:n
        S(i,j) = sum(bitand(M(:,i), M(:,j)) / sum(bitor(M(:,i), M(:,j)))); 
        %S(i,j) = (sum(bitand(M(:,i), M(:,j))) + sum(bitand(~M(:,i), ~M(:,j)))) / m;
        %S(i,j) = (1 + corr(M(:,i), M(:,j))) / 2; % for now Pearson's coef.
        %S(i,j) = 1 - (sum(bitxor(M(:,i), M(:,j))) / m);
        
        % simalarity have to be symetric
        S(j,i) = S(i,j);
    end
end


% then we compute Laplacian matrix from S
L = diag(diag(sum(S,2))) - S;

% then we compute an Eigenvalues and Eigenvectors
[V, D] = eig(L);

% then we choose the second smallest Eigenvalue and the coresponding
% Eigenvector (i.e. Fiedler's vector)
[~, perm] = sort(diag(D), 'ascend');
column = V(:, perm(2));

[~, perm] = sort(column, 'descend');
A = M(:, perm); % now, the columns are sorted, we need sort rows
permutace_y = permutace_y(perm);

%%
% simple sorting of rows, works good on simple examples
% tosort = [];
% for i=1:m
%     tosort(i, 1) = find(A(i,:), 1, 'first');
%     tosort(i, 2) = find(A(i,:), 1, 'last');
% end
%
% [~,perm] = sortrows(tosort);

%% bidirectional fixed permutation (Algorithm 2)

W = A;
% weights drives 0->1 and 1->0 flipping
W(W==1) = 1;
W(W==0) = -1;
tosort = [];

% solution of maximum subarray problem for each row
for i=1:m
    X = max_sub_array(W(i,:)); % Kadane s algorithm
    tosort(i,1) = X(1);
    tosort(i,2) = X(2);
end

[~, perm] = sortrows(tosort);
C = A(perm,:);

permutace_x = permutace_x(perm);

% % % % % Marketa
permutace = {permutace_x,permutace_y};
% % % % %

end

