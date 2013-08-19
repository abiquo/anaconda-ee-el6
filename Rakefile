task :updateimg do
  require 'fileutils'
  `dd if=/dev/zero of=/tmp/updates.img bs=1k count=2440`
  `mkfs.ext2 -F /tmp/updates.img`
  `sudo mount -o loop /tmp/updates.img /mnt/`
  Dir['anaconda-ee-13.21.195/*.py'].each do |f|
    FileUtils.cp f, '/mnt/'
  end
  Dir['anaconda-ee-13.21.195/ui/*'].each do |f|
    FileUtils.cp f, '/mnt/'
  end
  Dir['anaconda-ee-13.21.195/iw/*'].each do |f|
    FileUtils.cp f, '/mnt/'
  end
  Dir['anaconda-ee-13.21.195/installclasses/*'].each do |f|
    FileUtils.cp f, '/mnt/'
  end
  Dir['anaconda-ee-13.21.195/abiquo_upgrades/*'].each do |f|
    FileUtils.cp f, '/mnt/'
  end
  FileUtils.cp_r 'anaconda-ee-13.21.195/abiquo_upgrades', '/mnt'
  `sudo sync`
  `sudo umount /mnt/`
  `scp /tmp/updates.img root@mirror:/mirror/updates.img`
end
