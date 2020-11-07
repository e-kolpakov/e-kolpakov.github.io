#!/bin/bash

fullfile=$1

extension="${fullfile##*.}"
filename="${fullfile%%.*}"

convert $fullfile -resize 50% -sampling-factor 4:2:0 -strip -quality 85 -interlace JPEG -colorspace RGB "$filename@0,5x.$extension"
convert $fullfile -resize 25% -sampling-factor 4:2:0 -strip -quality 85 -interlace JPEG -colorspace RGB "$filename@0,25x.$extension"
convert $fullfile -resize 12.5% -sampling-factor 4:2:0 -strip -quality 85 -interlace JPEG -colorspace RGB "$filename@0,125x.$extension"