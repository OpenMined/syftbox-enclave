qemu-img resize image.vhd 30G
qemu-img convert -f raw -o subformat=fixed,force_size -O vpc image.raw image.vhd  
