from copy import deepcopy
import unittest

from apps.api.app.memory import FirestoreMissionRepository
from apps.api.app.mission_service import MissionService


class _Snapshot:
    def __init__(self, payload):
        self._payload = deepcopy(payload)
        self.exists = payload is not None

    def to_dict(self):
        return deepcopy(self._payload)


class _Document:
    def __init__(self, client, collection, document_id):
        self.client = client
        self.collection = collection
        self.document_id = document_id

    @property
    def key(self):
        return self.collection, self.document_id

    def get(self, transaction=None):
        return _Snapshot(self.client.store.get(self.key))


class _Query:
    def __init__(self, client, collection, descending=False, maximum=None):
        self.client = client
        self.collection = collection
        self.descending = descending
        self.maximum = maximum

    def order_by(self, field, direction=None):
        return _Query(
            self.client,
            self.collection,
            descending=direction == _Firestore.Query.DESCENDING,
            maximum=self.maximum,
        )

    def limit(self, maximum):
        return _Query(
            self.client,
            self.collection,
            descending=self.descending,
            maximum=maximum,
        )

    def stream(self):
        payloads = [
            deepcopy(value)
            for (collection, _), value in self.client.store.items()
            if collection == self.collection
        ]
        if self.descending:
            payloads.sort(key=lambda item: item.get("created_at", ""), reverse=True)
        if self.maximum is not None:
            payloads = payloads[:self.maximum]
        return iter(_Snapshot(payload) for payload in payloads)


class _Collection(_Query):
    def document(self, document_id):
        return _Document(self.client, self.collection, document_id)


class _Batch:
    def __init__(self, client):
        self.client = client
        self.operations = []

    def set(self, reference, payload, merge=False):
        self.operations.append(("set", reference, deepcopy(payload), merge))

    def create(self, reference, payload):
        self.operations.append(("create", reference, deepcopy(payload), False))

    def commit(self):
        for operation, reference, payload, merge in self.operations:
            if operation == "create" and reference.key in self.client.store:
                raise RuntimeError("document already exists")
            if merge:
                existing = deepcopy(self.client.store.get(reference.key, {}))
                existing.update(payload)
                payload = existing
            self.client.store[reference.key] = deepcopy(payload)


class _Transaction(_Batch):
    pass


class _Client:
    def __init__(self):
        self.store = {}
        self.closed = False

    def collection(self, name):
        return _Collection(self, name)

    def batch(self):
        return _Batch(self)

    def transaction(self, max_attempts=5):
        return _Transaction(self)

    def close(self):
        self.closed = True


class _Firestore:
    SERVER_TIMESTAMP = "server-timestamp"

    class Query:
        DESCENDING = "descending"

    @staticmethod
    def transactional(function):
        def wrapper(transaction):
            result = function(transaction)
            transaction.commit()
            return result

        return wrapper


class FirestoreMissionRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.client = _Client()
        self.repository = FirestoreMissionRepository(
            "test-project",
            client=self.client,
            firestore_module=_Firestore,
        )
        self.service = MissionService(self.repository)

    def test_mission_survives_repository_reconstruction(self):
        mission = self.service.start("Synthetic restart mission")
        reconstructed = FirestoreMissionRepository(
            "test-project",
            client=self.client,
            firestore_module=_Firestore,
        )
        self.assertEqual(reconstructed.get(mission.id), mission)

    def test_next_mission_retrieves_prior_receipt(self):
        first = self.service.start("First synthetic mission")
        second = self.service.start("Second synthetic mission")
        self.assertIn(
            first.receipt.receipt_sha256[:12],
            second.receipt.prior_memory_used,
        )

    def test_approval_transaction_is_idempotent(self):
        mission = self.service.start("Synthetic approval mission")
        mission.state = "approved"
        mission.approved_by = "judge"
        self.repository.record_approval(mission, "judge", "approved", "ui")
        self.repository.record_approval(mission, "judge", "approved", "ui")
        proof = self.repository.proof()
        self.assertEqual(proof["approval_count"], 1)
        self.assertEqual(self.repository.get(mission.id).state, "approved")

    def test_proof_reports_persistent_firestore(self):
        self.service.start("Synthetic proof mission")
        proof = self.repository.proof()
        self.assertEqual(proof["active_backend"], "firestore")
        self.assertTrue(proof["persistent"])
        self.assertFalse(proof["degraded"])
        self.assertEqual(proof["mission_count"], 1)


if __name__ == "__main__":
    unittest.main()
