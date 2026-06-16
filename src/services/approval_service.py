from datetime import datetime


class ApprovalService:
    """
    The 'Shenpi' Engine: Manages approval workflows (Digital Signatures).
    """

    def __init__(self, db_manager, notification_manager=None):
        self.db = db_manager
        self.notify = notification_manager
        # In-memory store for demo (would be DB table 'approvals' in prod)
        self.requests = []

    def create_request(self, requester_id, doc_type, doc_id, summary):
        """
        Creates a new approval request.
        """
        request = {
            "id": len(self.requests) + 1,
            "requester_id": requester_id,
            "doc_type": doc_type,
            "doc_id": doc_id,
            "summary": summary,
            "status": "Pending",
            "created_at": datetime.now(),
            "approver_id": None,
        }
        self.requests.append(request)

        if self.notify:
            self.notify.show_info(f"📋 New Approval Request: {summary}")

        return request["id"]

    def approve_request(self, request_id, approver_id):
        """
        Signs off on a request.
        """
        for req in self.requests:
            if req["id"] == request_id:
                req["status"] = "Approved"
                req["approver_id"] = approver_id
                req["approved_at"] = datetime.now()

                if self.notify:
                    self.notify.show_success(f"✅ Request #{request_id} Approved!")
                return True
        return False

    def reject_request(self, request_id, approver_id):
        for req in self.requests:
            if req["id"] == request_id:
                req["status"] = "Rejected"
                req["approver_id"] = approver_id
                if self.notify:
                    self.notify.show_error(f"❌ Request #{request_id} Rejected.")
                return True
        return False

    def get_pending_requests(self):
        return [r for r in self.requests if r["status"] == "Pending"]
