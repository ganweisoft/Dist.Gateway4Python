# using debian bookworm image
FROM debian:bookworm-slim

# Continue with application deployment
RUN mkdir /opt/ganwei
COPY IoTCenter.Python /opt/ganwei/IoTCenter.Python

WORKDIR /opt/ganwei/IoTCenter.Python/

CMD ["./CEquip"]