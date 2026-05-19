.PHONY: setup test replay-xprop replay-timing batch clean

setup:
	python -m pip install -r requirements.txt
	python -m pip install -e .

test:
	pytest -q

replay-xprop:
	gls-replay run scenarios/sample_xprop/scenario.yaml --out reports/xprop_report.md

replay-timing:
	gls-replay run scenarios/sample_timing/scenario.yaml --out reports/timing_report.md

batch:
	gls-replay batch scenarios --out reports/summary.md

clean:
	rm -f reports/*.md reports/*.json
