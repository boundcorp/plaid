format:
	black *.py

install:
	sudo cp openrgb.service /etc/systemd/system/openrgb.service
	sudo systemctl enable openrgb.service
	sudo cp plaid.service /etc/systemd/system/plaid.service
	sudo systemctl enable plaid.service

disable:
	sudo systemctl disable openrgb.service
	sudo systemctl disable plaid.service

uninstall:
	sudo systemctl disable openrgb.service
	sudo systemctl disable plaid.service
	sudo rm /etc/systemd/system/openrgb.service
	sudo rm /etc/systemd/system/plaid.service

start:
	sudo systemctl start openrgb
	sudo systemctl start plaid

stop:
	sudo systemctl stop plaid
	sudo systemctl stop openrgb

restart:
	sudo systemctl restart openrgb
	sudo systemctl restart plaid

status:
	sudo systemctl status openrgb
	sudo systemctl status plaid

logs:
	sudo journalctl -xeu plaid
