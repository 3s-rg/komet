FROM alpine:3.19

RUN apk add git build-base make python3 py3-pip py3-virtualenv py3-wheel
RUN apk add protobuf protobuf-c protobuf-c-dev protobuf-dev protoc 
RUN apk add pkgconfig libbsd-dev iproute2 nftables nftables-dev libcap-dev libnet libnet-dev libnl3 libnl3-dev gnutls-dev libbsd-dev

WORKDIR /app
RUN git clone --depth 1 --branch v3.19 https://github.com/checkpoint-restore/criu.git

RUN cat <<EOF > lfs64.patch
--- a/criu/include/restorer.h
+++ b/criu/include/restorer.h
@@ -177,7 +177,7 @@
 	struct rst_aio_ring *rings;
 	unsigned int rings_n;
 
-	struct rlimit64 *rlims;
+	struct rlimit *rlims;
 	unsigned int rlims_n;
 
 	pid_t *helpers /* the TASK_HELPERS to wait on at the end of restore */;
--- a/criu/include/fdinfo.h
+++ b/criu/include/fdinfo.h
@@ -10,7 +10,7 @@
 #include "images/timerfd.pb-c.h"
 
 struct fdinfo_common {
-	off64_t pos;
+	off_t pos;
 	int flags;
 	int mnt_id;
 	int owner;
--- a/criu/cr-restore.c
+++ b/criu/cr-restore.c
@@ -3172,9 +3172,9 @@
 {
 	int i;
 	TaskRlimitsEntry *rls = core->tc->rlimits;
-	struct rlimit64 *r;
+	struct rlimit *r;
 
-	ta->rlims = (struct rlimit64 *)rst_mem_align_cpos(RM_PRIVATE);
+	ta->rlims = (struct rlimit *)rst_mem_align_cpos(RM_PRIVATE);
 
 	if (!rls)
 		return prepare_rlimits_from_fd(pid, ta);
--- a/criu/cr-dump.c
+++ b/criu/cr-dump.c
@@ -358,7 +358,7 @@
 	int res;
 
 	for (res = 0; res < rls->n_rlimits; res++) {
-		struct rlimit64 lim;
+		struct rlimit lim;
 
 		if (syscall(__NR_prlimit64, pid, res, NULL, &lim)) {
 			pr_perror("Can't get rlimit %d", res);
--- a/criu/servicefd.c
+++ b/criu/servicefd.c
@@ -66,7 +66,7 @@
 
 int init_service_fd(void)
 {
-	struct rlimit64 rlimit;
+	struct rlimit rlimit;
 
 	/*
 	 * Service fd engine implies that file descriptors used won't be
EOF

WORKDIR /app/criu
RUN git apply /app/lfs64.patch
RUN make -j$(nproc)
