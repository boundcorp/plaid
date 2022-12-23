format:
	black *.py

install:
	sudo cp plaid.service /etc/systemd/system/plaid.service
	sudo systemctl enable plaid.service

disable:
	sudo systemctl disable plaid.service

uninstall:
	sudo systemctl disable plaid.service
	sudo rm /etc/systemd/system/plaid.service

start:
	sudo systemctl start plaid

stop:
	sudo systemctl stop plaid

restart:
	sudo systemctl restart plaid

status:
	sudo systemctl status plaid

logs:
	sudo journalctl -xeu plaid
