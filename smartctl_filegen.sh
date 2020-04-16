#!/bin/bash
if [ $# -eq 0 ]; then
    echo "No path given: outputting files to working directory"
    OUTPATH="."
elif [ $# -eq 1 ]; then
    echo "Outputting files to "$1
    OUTPATH="$(dirname $1)/$(basename $1)"
else
    echo -n "Unexpected number of parameters.\nUsage: sudo ./generate_files.sh /optional/path/to/files"
fi

[ ! -d $OUTPATH ] && mkdir $OUTPATH

# removing all old smartctl files before writing new ones
rm -f "$OUTPATH"/smartctl-dev-*.txt

DISKZ=($(lsblk -d -I 8 -o NAME -n))
echo Found $((${#DISKZ[@]})) disks
for d in "${DISKZ[@]}"; do
	  smartctl -x /dev/$d > "$OUTPATH/smartctl-dev-$d.txt"
done

exit 0
