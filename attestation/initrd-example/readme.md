

# TinyCore Linux kernel (very small)
wget http://tinycorelinux.net/14.x/x86_64/release/distribution_files/vmlinuz64



# Running the OS:
qemu-system-x86_64 -kernel vmlinuz64 -initrd initrd.img -nographic -append "console=ttyS0"