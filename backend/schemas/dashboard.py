from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_tickets: int
    open_tickets: int
    in_progress_tickets: int
    resolved_today: int
    critical_tickets: int
    unassigned_tickets: int
    tickets_by_status: dict
    tickets_by_priority: dict
    tickets_by_category: dict
    agent_workloads: list
    my_assigned_tickets: list
