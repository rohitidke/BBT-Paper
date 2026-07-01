function [A,permutace] = alternating(M, no_of_iterations)
%ALTERNATING 

A = double(M);
%no_of_iterations = 20;

% % % % % Marketa
permutace_x = (1 : size(A,1));
permutace_y = (1 : size(A,2))';
% % % % %

%% bidirectional fixed permutation (Algorithm 2)

for iter=1:no_of_iterations
    [m,n] = size(A);

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

    [~,perm] = sortrows(tosort);

    % % % % % Marketa
    if(rem(iter,2)==0)
        permutace_y = permutace_y(perm);
    else
        permutace_x = permutace_x(perm);
    end
    % % % % %

    A = A(perm,:);
    A = A';

end

% % % % % Marketa
permutace = {permutace_x,permutace_y};
% % % % %
end

