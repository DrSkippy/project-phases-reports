# brew install tree

tree -v --gitignore --charset utf-8 | sed 's/\xc2\xa0/ /g' > directory_tree.txt