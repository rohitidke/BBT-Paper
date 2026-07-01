function labeledMatrix = deleni(matrix, labeledMatrix, level, isColumnSplit, label, max_col, max_row, prah)
    
    [numRows, numCols] = size(matrix);


    % Matice obsahuje jen jednicky, nebo nuly (zde dat nejake kriterium
    % homogenity)
    if sum(matrix(:))/numel(matrix(:)) >= prah 
        labeledMatrix(:) = label; 
        return;
    end

    

    % Střídáme mezi dělením ve sloupcích a řádcích
    if isColumnSplit && numCols > max_col
        bestIndex = find_best_split(matrix, true);
        
        % Rekurzivní dělení na dvě podmatice
        labeledMatrix(:, 1:bestIndex) = deleni(matrix(:, 1:bestIndex), labeledMatrix(:, 1:bestIndex), level + 1, false, label * 2, max_col, max_row, prah);
        labeledMatrix(:, bestIndex+1:end) = deleni(matrix(:, bestIndex+1:end), labeledMatrix(:, bestIndex+1:end), level + 1, false, label * 2 + 1, max_col, max_row, prah);
    
    elseif ~isColumnSplit && numRows > max_row
        bestIndex = find_best_split(matrix, false);
        
        % Rekurzivní dělení na dvě podmatice
        labeledMatrix(1:bestIndex, :) = deleni(matrix(1:bestIndex, :), labeledMatrix(1:bestIndex, :), level + 1, true, label * 2, max_col, max_row, prah);
        labeledMatrix(bestIndex+1:end, :) = deleni(matrix(bestIndex+1:end, :), labeledMatrix(bestIndex+1:end, :), level + 1, true, label * 2 + 1, max_col, max_row, prah);
    end
end

function bestIndex = find_best_split(matrix, isColumnSplit)
    % Vybereme směr dělení
    if isColumnSplit
        numSplits = size(matrix, 2) - 1; % Počet možných dělení ve sloupcích
    else
        numSplits = size(matrix, 1) - 1; % Počet možných dělení v řádcích
    end

    bestIndex = 1;
    maxDiff = 0;

    % Projdeme všechny možnosti rozdělení
    for split = 1:numSplits
        if isColumnSplit
            group1 = matrix(:, 1:split);
            group2 = matrix(:, split+1:end);
        else
            group1 = matrix(1:split, :);
            group2 = matrix(split+1:end, :);
        end
        
        % % Spočítáme průměrné hodnoty obou skupin
        % mean1 = mean(group1(:));
        % mean2 = mean(group2(:));
        % % Měříme odlišnost pomocí absolutního rozdílu mezi průměry -- zde
        % % možné upravit
        % diff = abs(mean1 - mean2);

        % Mezitřídní variance - jako v Otsu
        n1 = numel(group1);
        n2 = numel(group2);
        n = n1 + n2;
        mean1 = mean(group1(:));
        mean2 = mean(group2(:));
        diff = (n1/n) * (n2/n) * (mean1 - mean2)^2;

        % % T statistika
        % var1 = var(group1(:));
        % var2 = var(group2(:));
        % mean1 = mean(group1(:));
        % mean2 = mean(group2(:));
        % n1 = numel(group1);
        % n2 = numel(group2);
        % diff = abs(mean1 - mean2) / sqrt(var1/n1 + var2/n2);
        
        % Uložíme nejlepší dělení
        if diff > maxDiff
            maxDiff = diff;
            bestIndex = split;
        end
    end
end