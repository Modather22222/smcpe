COBC=cobc
FLAGS=-free -b -O2 -Wall -I copybooks

all: libpayroll.so

libpayroll.so: payroll_calc.cob fx_norm.cob nsif_eng.cob tax_sud.cob esg_val.cob
	$(COBC) $(FLAGS) $^
	mv payroll_calc.so $@
	@echo "Built $@ ($$(stat -c%s $@) bytes)"

clean:
	rm -f *.so *.o payroll_calc.so libpayroll.so

test:
	python3 ../tests/test_cobol_roundtrip.py

.PHONY: all clean test
