# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import client_pb2 as client__pb2


class ClientStub(object):
    """This is a Client that calls the exthandler of FReD
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.CreateKeygroup = channel.unary_unary(
                '/mcc.fred.client.Client/CreateKeygroup',
                request_serializer=client__pb2.CreateKeygroupRequest.SerializeToString,
                response_deserializer=client__pb2.Empty.FromString,
                )
        self.DeleteKeygroup = channel.unary_unary(
                '/mcc.fred.client.Client/DeleteKeygroup',
                request_serializer=client__pb2.DeleteKeygroupRequest.SerializeToString,
                response_deserializer=client__pb2.Empty.FromString,
                )
        self.Read = channel.unary_unary(
                '/mcc.fred.client.Client/Read',
                request_serializer=client__pb2.ReadRequest.SerializeToString,
                response_deserializer=client__pb2.ReadResponse.FromString,
                )
        self.Scan = channel.unary_unary(
                '/mcc.fred.client.Client/Scan',
                request_serializer=client__pb2.ScanRequest.SerializeToString,
                response_deserializer=client__pb2.ScanResponse.FromString,
                )
        self.Update = channel.unary_unary(
                '/mcc.fred.client.Client/Update',
                request_serializer=client__pb2.UpdateRequest.SerializeToString,
                response_deserializer=client__pb2.UpdateResponse.FromString,
                )
        self.Delete = channel.unary_unary(
                '/mcc.fred.client.Client/Delete',
                request_serializer=client__pb2.DeleteRequest.SerializeToString,
                response_deserializer=client__pb2.DeleteResponse.FromString,
                )
        self.Append = channel.unary_unary(
                '/mcc.fred.client.Client/Append',
                request_serializer=client__pb2.AppendRequest.SerializeToString,
                response_deserializer=client__pb2.AppendResponse.FromString,
                )
        self.AddReplica = channel.unary_unary(
                '/mcc.fred.client.Client/AddReplica',
                request_serializer=client__pb2.AddReplicaRequest.SerializeToString,
                response_deserializer=client__pb2.Empty.FromString,
                )
        self.GetKeygroupInfo = channel.unary_unary(
                '/mcc.fred.client.Client/GetKeygroupInfo',
                request_serializer=client__pb2.GetKeygroupInfoRequest.SerializeToString,
                response_deserializer=client__pb2.GetKeygroupInfoResponse.FromString,
                )
        self.RemoveReplica = channel.unary_unary(
                '/mcc.fred.client.Client/RemoveReplica',
                request_serializer=client__pb2.RemoveReplicaRequest.SerializeToString,
                response_deserializer=client__pb2.Empty.FromString,
                )
        self.GetReplica = channel.unary_unary(
                '/mcc.fred.client.Client/GetReplica',
                request_serializer=client__pb2.GetReplicaRequest.SerializeToString,
                response_deserializer=client__pb2.GetReplicaResponse.FromString,
                )
        self.GetAllReplica = channel.unary_unary(
                '/mcc.fred.client.Client/GetAllReplica',
                request_serializer=client__pb2.Empty.SerializeToString,
                response_deserializer=client__pb2.GetAllReplicaResponse.FromString,
                )
        self.GetKeygroupTriggers = channel.unary_unary(
                '/mcc.fred.client.Client/GetKeygroupTriggers',
                request_serializer=client__pb2.GetKeygroupTriggerRequest.SerializeToString,
                response_deserializer=client__pb2.GetKeygroupTriggerResponse.FromString,
                )
        self.AddTrigger = channel.unary_unary(
                '/mcc.fred.client.Client/AddTrigger',
                request_serializer=client__pb2.AddTriggerRequest.SerializeToString,
                response_deserializer=client__pb2.Empty.FromString,
                )
        self.RemoveTrigger = channel.unary_unary(
                '/mcc.fred.client.Client/RemoveTrigger',
                request_serializer=client__pb2.RemoveTriggerRequest.SerializeToString,
                response_deserializer=client__pb2.Empty.FromString,
                )
        self.AddUser = channel.unary_unary(
                '/mcc.fred.client.Client/AddUser',
                request_serializer=client__pb2.AddUserRequest.SerializeToString,
                response_deserializer=client__pb2.Empty.FromString,
                )
        self.RemoveUser = channel.unary_unary(
                '/mcc.fred.client.Client/RemoveUser',
                request_serializer=client__pb2.RemoveUserRequest.SerializeToString,
                response_deserializer=client__pb2.Empty.FromString,
                )


class ClientServicer(object):
    """This is a Client that calls the exthandler of FReD
    """

    def CreateKeygroup(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def DeleteKeygroup(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Read(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Scan(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Update(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Delete(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Append(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def AddReplica(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetKeygroupInfo(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def RemoveReplica(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetReplica(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetAllReplica(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetKeygroupTriggers(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def AddTrigger(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def RemoveTrigger(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def AddUser(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def RemoveUser(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_ClientServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'CreateKeygroup': grpc.unary_unary_rpc_method_handler(
                    servicer.CreateKeygroup,
                    request_deserializer=client__pb2.CreateKeygroupRequest.FromString,
                    response_serializer=client__pb2.Empty.SerializeToString,
            ),
            'DeleteKeygroup': grpc.unary_unary_rpc_method_handler(
                    servicer.DeleteKeygroup,
                    request_deserializer=client__pb2.DeleteKeygroupRequest.FromString,
                    response_serializer=client__pb2.Empty.SerializeToString,
            ),
            'Read': grpc.unary_unary_rpc_method_handler(
                    servicer.Read,
                    request_deserializer=client__pb2.ReadRequest.FromString,
                    response_serializer=client__pb2.ReadResponse.SerializeToString,
            ),
            'Scan': grpc.unary_unary_rpc_method_handler(
                    servicer.Scan,
                    request_deserializer=client__pb2.ScanRequest.FromString,
                    response_serializer=client__pb2.ScanResponse.SerializeToString,
            ),
            'Update': grpc.unary_unary_rpc_method_handler(
                    servicer.Update,
                    request_deserializer=client__pb2.UpdateRequest.FromString,
                    response_serializer=client__pb2.UpdateResponse.SerializeToString,
            ),
            'Delete': grpc.unary_unary_rpc_method_handler(
                    servicer.Delete,
                    request_deserializer=client__pb2.DeleteRequest.FromString,
                    response_serializer=client__pb2.DeleteResponse.SerializeToString,
            ),
            'Append': grpc.unary_unary_rpc_method_handler(
                    servicer.Append,
                    request_deserializer=client__pb2.AppendRequest.FromString,
                    response_serializer=client__pb2.AppendResponse.SerializeToString,
            ),
            'AddReplica': grpc.unary_unary_rpc_method_handler(
                    servicer.AddReplica,
                    request_deserializer=client__pb2.AddReplicaRequest.FromString,
                    response_serializer=client__pb2.Empty.SerializeToString,
            ),
            'GetKeygroupInfo': grpc.unary_unary_rpc_method_handler(
                    servicer.GetKeygroupInfo,
                    request_deserializer=client__pb2.GetKeygroupInfoRequest.FromString,
                    response_serializer=client__pb2.GetKeygroupInfoResponse.SerializeToString,
            ),
            'RemoveReplica': grpc.unary_unary_rpc_method_handler(
                    servicer.RemoveReplica,
                    request_deserializer=client__pb2.RemoveReplicaRequest.FromString,
                    response_serializer=client__pb2.Empty.SerializeToString,
            ),
            'GetReplica': grpc.unary_unary_rpc_method_handler(
                    servicer.GetReplica,
                    request_deserializer=client__pb2.GetReplicaRequest.FromString,
                    response_serializer=client__pb2.GetReplicaResponse.SerializeToString,
            ),
            'GetAllReplica': grpc.unary_unary_rpc_method_handler(
                    servicer.GetAllReplica,
                    request_deserializer=client__pb2.Empty.FromString,
                    response_serializer=client__pb2.GetAllReplicaResponse.SerializeToString,
            ),
            'GetKeygroupTriggers': grpc.unary_unary_rpc_method_handler(
                    servicer.GetKeygroupTriggers,
                    request_deserializer=client__pb2.GetKeygroupTriggerRequest.FromString,
                    response_serializer=client__pb2.GetKeygroupTriggerResponse.SerializeToString,
            ),
            'AddTrigger': grpc.unary_unary_rpc_method_handler(
                    servicer.AddTrigger,
                    request_deserializer=client__pb2.AddTriggerRequest.FromString,
                    response_serializer=client__pb2.Empty.SerializeToString,
            ),
            'RemoveTrigger': grpc.unary_unary_rpc_method_handler(
                    servicer.RemoveTrigger,
                    request_deserializer=client__pb2.RemoveTriggerRequest.FromString,
                    response_serializer=client__pb2.Empty.SerializeToString,
            ),
            'AddUser': grpc.unary_unary_rpc_method_handler(
                    servicer.AddUser,
                    request_deserializer=client__pb2.AddUserRequest.FromString,
                    response_serializer=client__pb2.Empty.SerializeToString,
            ),
            'RemoveUser': grpc.unary_unary_rpc_method_handler(
                    servicer.RemoveUser,
                    request_deserializer=client__pb2.RemoveUserRequest.FromString,
                    response_serializer=client__pb2.Empty.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'mcc.fred.client.Client', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Client(object):
    """This is a Client that calls the exthandler of FReD
    """

    @staticmethod
    def CreateKeygroup(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/mcc.fred.client.Client/CreateKeygroup',
            client__pb2.CreateKeygroupRequest.SerializeToString,
            client__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def DeleteKeygroup(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/mcc.fred.client.Client/DeleteKeygroup',
            client__pb2.DeleteKeygroupRequest.SerializeToString,
            client__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Read(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/mcc.fred.client.Client/Read',
            client__pb2.ReadRequest.SerializeToString,
            client__pb2.ReadResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Scan(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/mcc.fred.client.Client/Scan',
            client__pb2.ScanRequest.SerializeToString,
            client__pb2.ScanResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Update(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/mcc.fred.client.Client/Update',
            client__pb2.UpdateRequest.SerializeToString,
            client__pb2.UpdateResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Delete(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/mcc.fred.client.Client/Delete',
            client__pb2.DeleteRequest.SerializeToString,
            client__pb2.DeleteResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Append(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/mcc.fred.client.Client/Append',
            client__pb2.AppendRequest.SerializeToString,
            client__pb2.AppendResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def AddReplica(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/mcc.fred.client.Client/AddReplica',
            client__pb2.AddReplicaRequest.SerializeToString,
            client__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetKeygroupInfo(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/mcc.fred.client.Client/GetKeygroupInfo',
            client__pb2.GetKeygroupInfoRequest.SerializeToString,
            client__pb2.GetKeygroupInfoResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def RemoveReplica(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/mcc.fred.client.Client/RemoveReplica',
            client__pb2.RemoveReplicaRequest.SerializeToString,
            client__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetReplica(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/mcc.fred.client.Client/GetReplica',
            client__pb2.GetReplicaRequest.SerializeToString,
            client__pb2.GetReplicaResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetAllReplica(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/mcc.fred.client.Client/GetAllReplica',
            client__pb2.Empty.SerializeToString,
            client__pb2.GetAllReplicaResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetKeygroupTriggers(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/mcc.fred.client.Client/GetKeygroupTriggers',
            client__pb2.GetKeygroupTriggerRequest.SerializeToString,
            client__pb2.GetKeygroupTriggerResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def AddTrigger(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/mcc.fred.client.Client/AddTrigger',
            client__pb2.AddTriggerRequest.SerializeToString,
            client__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def RemoveTrigger(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/mcc.fred.client.Client/RemoveTrigger',
            client__pb2.RemoveTriggerRequest.SerializeToString,
            client__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def AddUser(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/mcc.fred.client.Client/AddUser',
            client__pb2.AddUserRequest.SerializeToString,
            client__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def RemoveUser(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/mcc.fred.client.Client/RemoveUser',
            client__pb2.RemoveUserRequest.SerializeToString,
            client__pb2.Empty.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)