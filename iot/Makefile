CERTS_DIR := $(PWD)/certs
FRED_VERSION := 0.2.19

.PHONY: all

all: sensor/sensor.img satellite/satellite.img nameservice/nase.img orchestrator/orchestrator.img traj.zip traj-tiny.zip

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

sensor/sensor.bin: sensor/sensor.go sensor/go.mod
	cd $(@D) && GOOS=linux GOARCH=amd64 go build -o $(@F) $(<F)

sensor/sensor.img: sensor/sensor.sh sensor/sensor.bin sensor/sensor-base.sh
	@docker run -it --platform=linux/amd64 --rm \
	-v $(abspath $(@D))/sensor.sh:/app.sh \
	-v $(abspath $(@D))/sensor-base.sh:/base.sh \
	-v $(abspath $(@D))/sensor.bin:/files/sensor.bin \
	-v $(PWD):/opt/code \
	--privileged rootfsbuilder $@

orchestrator/proto/client_pb2.py orchestrator/proto/client_pb2_grpc.py: # download proto from gitlab
	mkdir -p orchestrator/proto
	curl -sSL https://github.com/OpenFogStack/FReD/archive/refs/tags/v${FRED_VERSION}.tar.gz --output /tmp/fred.tar.gz
	tar -xvf /tmp/fred.tar.gz -C /tmp/
	mv /tmp/FReD-${FRED_VERSION}/proto/client/client_pb2*.py $(@D)
	rm -rf /tmp/FReD-${FRED_VERSION}

orchestrator/tflite_runtime-2.17.0-cp311-cp311-linux_x86_64.whl: orchestrator/tf-alpine-3.19.patch
	docker run --platform linux/amd64 \
		-v $(abspath $(@D)):/orchestrator \
		-v $(abspath $(@D))/$(<F):/$(<F):ro \
		--rm alpine:3.19  \
		/bin/sh -c "apk add --update --no-cache \
			curl \
			git \
			python3 \
			py3-pip \
			python3-dev \
			py3-numpy \
			make \
			cmake \
			gcc \
			g++ \
			swig \
			libjpeg-turbo-dev \
			zlib-dev \
			bash \
			linux-headers \
			py3-numpy-dev \
			py3-numpy \
			py3-pybind11 \
			py3-pybind11-dev \
			py3-wheel \
			py3-setuptools\
			&& git clone https://github.com/tensorflow/tensorflow.git --branch v2.16.1 --depth 1 \
			&& cd tensorflow \
			&& git apply /$(<F) \
			&& bash tensorflow/lite/tools/pip_package/build_pip_package_with_cmake.sh \
			&& cp /tensorflow/tensorflow/lite/tools/pip_package/gen/tflite_pip/python3/dist/$(@F) /$@ \
			&& exit 0"

orchestrator/libgcc_s.so.1 lib orchestrator/libstdc++.so.6.0.32:
	docker run --platform linux/amd64 --name tmp -d alpine:3.19 tail -f /dev/null
	docker exec tmp apk add --no-cache libstdc++==13.2.1_git20231014-r0
	docker cp tmp:/usr/lib/libstdc++.so.6.0.32 $(@D)/libstdc++.so.6.0.32
	docker cp tmp:/usr/lib/libgcc_s.so.1 $(@D)/libgcc_s.so.1
	docker rm -f tmp

orchestrator/%.zip: orchestrator/tflite_runtime-2.17.0-cp311-cp311-linux_x86_64.whl ${CERTS_DIR}/client.crt ${CERTS_DIR}/client.key ${CERTS_DIR}/ca.crt orchestrator/%.py orchestrator/proto/client_pb2.py orchestrator/proto/client_pb2_grpc.py orchestrator/libgcc_s.so.1 orchestrator/libstdc++.so.6.0.32 orchestrator/model.tflite
	mkdir -p $(@D)/$*
	cp $(@D)/$*.py $(@D)/$*/fn.py
	docker run --platform linux/amd64 --rm \
		-v $(abspath $(@D))/$*:/app \
		-v $(abspath $(@D)):/$(@D):ro \
		-w / python:3.11-alpine \
		python3 -m pip install numpy==1.26.4 grpcio==1.56.0 protobuf==4.23.3 /$< --target /app
	cp ${CERTS_DIR}/client.crt $(@D)/$*/cert.crt
	cp ${CERTS_DIR}/client.key $(@D)/$*/cert.key
	cp ${CERTS_DIR}/ca.crt $(@D)/$*/ca.crt
	cp $(@D)/libgcc_s.so.1 $(@D)/$*/libgcc_s.so.1
	cp $(@D)/libstdc++.so.6.0.32 $(@D)/$*/libstdc++.so.6.0.32
	cp $(@D)/model.tflite $(@D)/$*/model.tflite
	mkdir -p $(@D)/$*/proto
	cp $(@D)/proto/client_pb2.py $(@D)/$*/client_pb2.py
	cp $(@D)/proto/client_pb2_grpc.py $(@D)/$*/client_pb2_grpc.py
	cd $(@D)/$* && zip -r ../$*.zip .
	rm -rf $(@D)/$*

orchestrator/orchestrator.img: orchestrator/orchestrator.sh orchestrator/orchestrator-base.sh orchestrator/orchestrator.py ${CERTS_DIR}/client.crt ${CERTS_DIR}/client.key ${CERTS_DIR}/ca.crt orchestrator/fn.zip orchestrator/proto/client_pb2.py orchestrator/proto/client_pb2_grpc.py
	@docker run -it --platform=linux/amd64 --rm \
	-v $(abspath $(@D))/orchestrator.sh:/app.sh \
	-v $(abspath $(@D))/orchestrator-base.sh:/base.sh \
	-v $(abspath $(@D))/orchestrator.py:/files/orchestrator.py \
	-v $(abspath $(@D))/proto/client_pb2.py:/files/client_pb2.py \
	-v $(abspath $(@D))/proto/client_pb2_grpc.py:/files/client_pb2_grpc.py \
	-v ${CERTS_DIR}/client.crt:/files/client.crt \
	-v ${CERTS_DIR}/client.key:/files/client.key \
	-v ${CERTS_DIR}/ca.crt:/files/ca.crt \
	-v $(abspath $(@D))/fn.zip:/files/fn.zip \
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

traj-full.zip: config-full.toml
	@docker run --rm -v $(PWD):/app satgen-docker /app/$< /app/$@

traj-tiny.zip: config-tiny.toml
	@docker run --rm -v $(PWD):/app satgen-docker /app/$< /app/$@
