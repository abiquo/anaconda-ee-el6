include ../Makefile.inc

all:
	echo "nothing to make"

install: 
	mkdir -p $(DESTDIR)/$(PYTHONLIBDIR)/abiquo_upgrades
	install *.py $(DESTDIR)/$(PYTHONLIBDIR)/abiquo_upgrades
	../py-compile --basedir $(DESTDIR)/$(PYTHONLIBDIR)/abiquo_upgrades $(DESTDIR)/$(PYTHONLIBDIR)/abiquo_upgrades/*.py

clean:
	rm -f *.o *.so *.pyc

depend:
