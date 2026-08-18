#!/bin/bash

cp ./templates/*template* .

for f in *.template; do
    mv "$f" "${f%.template}"
done

echo "Python scripts ready for use!"
