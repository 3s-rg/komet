CERTS_DIR := $(PWD)/certs
FRED_VERSION := 0.2.19

.PHONY: all

all: client/client.img satellite/satellite.img nameservice/nase.img orchestrator/orchestrator.img traj.zip

${CERTS_DIR}/ca.key:
	@mkdir -p ${CERTS_DIR}
	@openssl genrsa -out $@ 2048

${CERTS_DIR}/ca.crt: ${CERTS_DIR}/ca.key
	@mkdir -p ${CERTS_DIR}
	@openssl req -x509 -new -nodes -key $< -days 1825 -sha512 -out $@ -subj "/C=DE/L=Berlin/O=OpenFogStack/OU=komet"

${CERTS_DIR}/nase.key ${CERTS_DIR}/nase.crt: ${CERTS_DIR}/ca.crt
	@mkdir -p ${CERTS_DIR}
	./gen-fred-cert.sh ${CERTS_DIR} nase 127.0.0.1

${CERTS_DIR}/client.key ${CERTS_DIR}/client.crt: ${CERTS_DIR}/ca.crt
	@mkdir -p ${CERTS_DIR}
	./gen-fred-cert.sh ${CERTS_DIR} client 127.0.0.1 172.18.0.1

${CERTS_DIR}/fred.key ${CERTS_DIR}/fred.crt: ${CERTS_DIR}/ca.crt
	@mkdir -p ${CERTS_DIR}
	./gen-fred-cert.sh ${CERTS_DIR} fred 127.0.0.1

client/client.bin: client/client.go client/go.mod
	cd $(@D) && GOOS=linux GOARCH=amd64 go build -o $(@F) $(<F)

client/client.img: client/client.sh client/client.bin client/client-base.sh cfg.txt
	@docker run -it --platform=linux/amd64 --rm \
	-v $(abspath $(@D))/client.sh:/app.sh \
	-v $(abspath $(@D))/client-base.sh:/base.sh \
	-v $(abspath $(@D))/client.bin:/files/client.bin \
	-v $(PWD)/cfg.txt:/files/cfg.txt \
	-v $(PWD):/opt/code \
	--privileged rootfsbuilder $@

orchestrator/proto/client_pb2.py orchestrator/proto/client_pb2_grpc.py: # download proto from gitlab
	mkdir -p orchestrator/proto
	curl -sSL https://github.com/OpenFogStack/FReD/archive/refs/tags/v${FRED_VERSION}.tar.gz --output /tmp/fred.tar.gz
	tar -xvf /tmp/fred.tar.gz -C /tmp/
	mv /tmp/FReD-${FRED_VERSION}/proto/client/client_pb2*.py $(@D)
	rm -rf /tmp/FReD-${FRED_VERSION}

orchestrator/%.zip: ${CERTS_DIR}/client.crt ${CERTS_DIR}/client.key ${CERTS_DIR}/ca.crt orchestrator/%.py orchestrator/proto/client_pb2.py orchestrator/proto/client_pb2_grpc.py
	mkdir -p $(@D)/$*
	cp $(@D)/$*.py $(@D)/$*/fn.py
	docker run --platform linux/amd64 --rm \
		-v $(abspath $(@D))/$*:/app \
		-v $(abspath $(@D)):/$(@D):ro \
		-w / python:3.11-alpine \
		python3 -m pip install grpcio==1.56.0 protobuf==4.23.3 --target /app
	cp ${CERTS_DIR}/client.crt $(@D)/$*/cert.crt
	cp ${CERTS_DIR}/client.key $(@D)/$*/cert.key
	cp ${CERTS_DIR}/ca.crt $(@D)/$*/ca.crt
	mkdir -p $(@D)/$*/proto
	cp $(@D)/proto/client_pb2.py $(@D)/$*/client_pb2.py
	cp $(@D)/proto/client_pb2_grpc.py $(@D)/$*/client_pb2_grpc.py
	cd $(@D)/$* && zip -r ../$*.zip .
	rm -rf $(@D)/$*

orchestrator/orchestrator.img: orchestrator/orchestrator.sh orchestrator/orchestrator-base.sh orchestrator/orchestrator.py ${CERTS_DIR}/client.crt ${CERTS_DIR}/client.key ${CERTS_DIR}/ca.crt orchestrator/get_fn.zip orchestrator/put_count.zip orchestrator/proto/client_pb2.py orchestrator/proto/client_pb2_grpc.py
	@docker run -it --platform=linux/amd64 --rm \
		-v $(abspath $(@D))/orchestrator.sh:/app.sh \
		-v $(abspath $(@D))/orchestrator-base.sh:/base.sh \
		-v $(abspath $(@D))/orchestrator.py:/files/orchestrator.py \
		-v $(abspath $(@D))/proto/client_pb2.py:/files/client_pb2.py \
		-v $(abspath $(@D))/proto/client_pb2_grpc.py:/files/client_pb2_grpc.py \
		-v ${CERTS_DIR}/client.crt:/files/client.crt \
		-v ${CERTS_DIR}/client.key:/files/client.key \
		-v ${CERTS_DIR}/ca.crt:/files/ca.crt \
		-v $(abspath $(@D))/get_fn.zip:/files/get_fn.zip \
		-v $(abspath $(@D))/put_count.zip:/files/put_count.zip \
		-v $(PWD):/opt/code \
		--privileged rootfsbuilder $@

satellite/alexandra.bin: # download alexandra from image
	docker create --name alexandra-tmp git.tu-berlin.de:5000/mcc-fred/fred/alexandra:v${FRED_VERSION}
	docker cp alexandra-tmp:/alexandra $@
	docker rm -f alexandra-tmp

satellite/fred.bin: # download fred from image
	docker create --name fred-tmp git.tu-berlin.de:5000/mcc-fred/fred/fred:v${FRED_VERSION}
	docker cp fred-tmp:/fred $@
	docker rm -f fred-tmp

satellite/satellite.img: satellite/satellite.sh satellite/satellite-base.sh ${CERTS_DIR}/fred.crt ${CERTS_DIR}/fred.key ${CERTS_DIR}/client.crt ${CERTS_DIR}/client.key ${CERTS_DIR}/ca.crt satellite/fred.bin satellite/alexandra.bin satellite/tf-linux-amd64.bin
	@docker run -it --platform=linux/amd64 --rm \
		-v $(abspath $(@D))/satellite.sh:/app.sh \
		-v $(abspath $(@D))/satellite-base.sh:/base.sh \
		-v $(abspath $(@D))/fred.bin:/files/fred \
		-v $(abspath $(@D))/alexandra.bin:/files/alexandra \
		-v $(abspath $(@D))/tf-linux-amd64.bin:/files/tf-linux-amd64 \
		-v ${CERTS_DIR}/fred.crt:/files/fred.crt \
		-v ${CERTS_DIR}/fred.key:/files/fred.key \
		-v ${CERTS_DIR}/client.crt:/files/client.crt \
		-v ${CERTS_DIR}/client.key:/files/client.key \
		-v ${CERTS_DIR}/ca.crt:/files/ca.crt \
		-v $(PWD):/opt/code \
		--privileged rootfsbuilder $@

nameservice/etcd.bin: # download etcd
	curl -SL https://github.com/etcd-io/etcd/releases/download/v3.5.7/etcd-v3.5.7-linux-amd64.tar.gz --output /tmp/etcd-v3.5.7-linux-amd64.tar.gz
	tar -xvf /tmp/etcd-v3.5.7-linux-amd64.tar.gz -C /tmp
	mv /tmp/etcd-v3.5.7-linux-amd64/etcd $@
	# rm -rf /tmp/etcd-v3.5.7-linux-amd64
	# rm /tmp/etcd-v3.5.7-linux-amd64.tar.gz

nameservice/nase.img: nameservice/nase.sh nameservice/nase-base.sh ${CERTS_DIR}/nase.crt ${CERTS_DIR}/nase.key ${CERTS_DIR}/ca.crt nameservice/etcd.bin
	@docker run -it --platform=linux/amd64 --rm \
		-v $(abspath $(@D))/nase.sh:/app.sh \
		-v $(abspath $(@D))/nase-base.sh:/base.sh \
		-v $(abspath $(@D))/etcd.bin:/files/etcd \
		-v ${CERTS_DIR}/nase.crt:/files/nase.crt \
		-v ${CERTS_DIR}/nase.key:/files/nase.key \
		-v ${CERTS_DIR}/ca.crt:/files/ca.crt \
		-v $(PWD):/opt/code \
		--privileged rootfsbuilder $@

traj.zip: config.toml
	@docker run --rm -v $(PWD):/app satgen-docker /app/$< /app/$@
