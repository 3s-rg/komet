.PHONY: all

all: client/client.img criu/criu.img

client/client.img: client/client.sh client/criu-client.py client/client-base.sh cfg.txt ../komet/komet.py
	@docker run -it --platform=linux/amd64 --rm \
		-v $(PWD)/client/client.sh:/app.sh \
		-v $(PWD)/client/criu-client.py:/files/criu-client.py \
		-v $(PWD)/client/client-base.sh:/base.sh \
		-v $(PWD)/cfg.txt:/files/cfg.txt \
		-v $(PWD)/../komet/komet.py:/files/komet.py \
		-v $(PWD):/opt/code \
		--privileged rootfsbuilder $@

criu/criu.img: criu/criu.sh criu/criu-base.sh criu/server.py criu/redis-alpine-amd64.tar.gz
	@docker run -it --platform=linux/amd64 --rm \
		-v $(PWD)/criu/criu.sh:/app.sh \
		-v $(PWD)/criu/criu-base.sh:/base.sh \
		-v $(PWD)/criu/server.py:/files/server.py \
		-v $(PWD)/criu/redis-alpine-amd64.tar.gz:/files/redis-alpine-amd64.tar.gz \
		-v $(PWD):/opt/code \
		--privileged rootfsbuilder $@

traj.zip: config.toml
	@docker run --rm -v $(PWD):/app satgen-docker /app/$< /app/$@

# criu/criu-%.bin: criu.Dockerfile
# 	docker build --platform=linux/$* -t criu-builder -f $< .
# 	docker create --platform=linux/$* --name criu criu-builder
# 	docker cp criu:/app/criu/criu/criu $@
# 	docker rm criu

criu/redis-alpine-%.tar.gz:
	docker image pull --platform=linux/$* redis:alpine
	docker save --output $@ redis:alpine
