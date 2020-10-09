.PHONY: test ring ringv

default: test

ring:
	./p2pnetwork.py -n 3

ringv:
	./p2pnetwork.py -n 10 -v

test:
	coverage run -m router_test

coverage:
	coverage report -m
