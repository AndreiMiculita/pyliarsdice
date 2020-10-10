for i in *.gif ; do gif2webp "$i" -o "${i%.*}.webp" ; done

