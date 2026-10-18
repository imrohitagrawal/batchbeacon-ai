"""Generated SDK recording transport + explicit MVCC simulation, NOT Firestore.

Independent clients share this fake server. Emulator/cloud checks are separate.
The production adapter does not use this process-local lock or memory state.
"""

from datetime import UTC, datetime
from threading import RLock

from google.api_core import exceptions
from google.api_core.client_options import ClientOptions
from google.auth.credentials import AnonymousCredentials
from google.cloud.firestore_v1.services.firestore import FirestoreClient
from google.cloud.firestore_v1.services.firestore.transports.base import FirestoreTransport
from google.cloud.firestore_v1.types import (
    BatchGetDocumentsResponse,
    BeginTransactionResponse,
    CommitResponse,
    Document,
)


class Server:
    def __init__(self):
        self.docs, self.versions, self.transactions, self.calls = {}, {}, {}, []
        self.lock, self.counter = RLock(), 0
        self.before_commit = lambda request: None
        self.after_commit = lambda request: None
        self.read_transform = lambda responses: responses
        self.fail, self.rollback_fails, self.aborts = None, False, 0
        self.clock = lambda: datetime.now(UTC)

    def seed(self, document):
        with self.lock:
            saved = Document(document)
            timestamp = self.clock()
            saved.create_time = (self.docs[document.name].create_time if document.name in self.docs
                                 else timestamp)
            saved.update_time = timestamp
            self.docs[document.name] = saved
            self.versions[document.name] = self.versions.get(document.name, 0) + 1

    def rpc(self, name, request, **options):
        assert options["retry"] is None and 0 < options["timeout"] <= 15
        self.calls.append((name, request, options))
        if self.fail == name:
            raise exceptions.ServiceUnavailable("injected unavailable")
        if name == "begin_transaction":
            with self.lock:
                self.counter += 1
                key = str(self.counter).encode()
                self.transactions[key] = ({k: Document(v) for k, v in self.docs.items()},
                                           self.versions.copy(), set())
            return BeginTransactionResponse(transaction=key)
        if name == "batch_get_documents":
            docs, _, reads = self.transactions[request.transaction]
            reads.update(request.documents)
            responses = [BatchGetDocumentsResponse(found=docs[n]) if n in docs else
                         BatchGetDocumentsResponse(missing=n) for n in reversed(request.documents)]
            return iter(self.read_transform(responses))
        if name == "rollback":
            if self.rollback_fails:
                raise exceptions.ServiceUnavailable("injected rollback failure")
            return None
        assert name == "commit"
        self.before_commit(request)
        with self.lock:
            _, versions, reads = self.transactions[request.transaction]
            if any(versions.get(n, 0) != self.versions.get(n, 0) for n in reads):
                self.aborts += 1
                raise exceptions.Aborted("injected snapshot conflict")
            for write in request.writes:
                if (write.update.name in self.docs) != write.current_document.exists:
                    raise exceptions.FailedPrecondition("injected existence conflict")
            for write in request.writes:
                self.seed(write.update)
        self.after_commit(request)
        return CommitResponse(commit_time=self.clock())


class RecordingTransport(FirestoreTransport):
    def __init__(self, server, endpoint):
        super().__init__(host=endpoint, credentials=AnonymousCredentials())
        self.server = server
        self.functions = {name: self._function(name) for name in (
            "begin_transaction", "batch_get_documents", "commit", "rollback")}
        self._wrapped_methods = {func: func for func in self.functions.values()}

    def _function(self, name):
        return lambda request, **kwargs: self.server.rpc(name, request, **kwargs)

    @property
    def begin_transaction(self):
        return self.functions["begin_transaction"]

    @property
    def batch_get_documents(self):
        return self.functions["batch_get_documents"]

    @property
    def commit(self):
        return self.functions["commit"]

    @property
    def rollback(self):
        return self.functions["rollback"]


def client(server, endpoint="127.0.0.1:8088"):
    return FirestoreClient(transport=RecordingTransport(server, endpoint),
                           client_options=ClientOptions(api_endpoint=endpoint))
