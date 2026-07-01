function B = max_sub_array(A)
% Kadane s algorithm

n = length(A);
max_ending_here = A(1);
max_so_far = A(1);

begin = 1;
ending = 1;

for x = 2:n
    a = A(x);
    b = max_ending_here + A(x);
    max_ending_here = max(a, b);
    
    if max_ending_here >= max_so_far
        ending = x;
        max_so_far = max_ending_here;
    end
    
    if max_so_far == A(x)
        begin = x;
        ending = x;
    end
end

B = [begin, ending];

end