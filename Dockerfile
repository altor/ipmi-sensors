FROM debian:buster
RUN apt update && apt install -y python3 python3-pymongo ipmitool
COPY ./ipmi_sensor.py /usr/bin/ipmi_sensor.py


ENTRYPOINT ["python3", "/usr/bin/ipmi_sensor.py"]
