function [A, permutace] = barycenter(M)
%BARYCENTER 

[m, n] = size(M);
indexes = 1:max(m,n);
A = M;
old = M;
iter = 1;
% % % % % Marketa
permutace_x = (1 : size(A,1));
permutace_y = (1 : size(A,2))';
% % % % %

% until the algorithm converge
while 1
    iter = iter + 1;
    cost = zeros(size(A,1), 1); % barycenters
    
    % this can be easily vectorized for speed
    for i=1:size(A,1)
        cost(i) = sum(A(i,:) .* indexes(1:size(A,2))) / sum(A(i,:));
    end
    
    [~, perm] = sort(cost, 'ascend'); % check if direction plays a role

    % % % % % Marketa
    if(rem(iter,2)==1)
        permutace_y = permutace_y(perm);
    else
        permutace_x = permutace_x(perm);
    end
    % % % % %

    B = A(perm,:);
    
    % if the result is not changig, stop
    if all(all(old==B))
        break;
    end
    
    A = B';
    old = A;
end

[m, n] = size(A);

% if the result is transposed
if(m < n) 
    A = A';
end

% % % % % Marketa
permutace = {permutace_x,permutace_y};
% % % % %

end

