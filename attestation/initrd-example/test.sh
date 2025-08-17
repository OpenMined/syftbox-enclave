# Compile statically
GOOS=linux GOARCH=amd64 CGO_ENABLED=0 go build -o init init.go

# Remove existing initrd directory if it exists
rm -rf initrd
rm -f initrd.img

# Create minimal initrd
mkdir -p initrd
cp init initrd/init
chmod +x initrd/init
cd initrd
find . | cpio -o -H newc | gzip > ../initrd.img
cd ..
