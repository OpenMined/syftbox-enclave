uv run sev-snp-measure \
  --mode snp \
  --vcpus 1 \
  --vcpu-type EPYC-Milan \
  --ovmf /home/azureuser/edk2/Build/AmdSev/DEBUG_GCC5/FV/OVMF.fd \
  --kernel ./image.vmlinuz \
  --initrd ./image.initrd \
  --append "console=ttyS0 earlyprintk=ttyS0 rootdelay=300 root=LABEL=root rw"