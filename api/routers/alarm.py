from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException

from api.dependencies import InjectedAlarmRepository

router = APIRouter(prefix="/alarms", tags=["Alarms"])

alarms_store: dict[UUID, dict] = {}


@router.get("")
def list_alarms(repository: InjectedAlarmRepository):
    alarms = repository.find_all()

    return {"alarms": alarms}


@router.post("", status_code=201)
def create_alarm(alarm_data: dict):
    alarm_id = uuid4()
    alarm = {"id": str(alarm_id), "status": "scheduled", **alarm_data}
    alarms_store[alarm_id] = alarm
    return alarm


@router.get("/{alarm_id}")
def get_alarm(alarm_id: UUID):
    if alarm_id not in alarms_store:
        raise HTTPException(status_code=404, detail="Alarm not found")
    return alarms_store[alarm_id]


@router.put("/{alarm_id}")
def update_alarm(alarm_id: UUID, alarm_data: dict):
    if alarm_id not in alarms_store:
        raise HTTPException(status_code=404, detail="Alarm not found")

    alarms_store[alarm_id].update(alarm_data)
    return alarms_store[alarm_id]


@router.delete("/{alarm_id}", status_code=204)
def delete_alarm(alarm_id: UUID):
    if alarm_id not in alarms_store:
        raise HTTPException(status_code=404, detail="Alarm not found")

    del alarms_store[alarm_id]


@router.post("/{alarm_id}/cancel")
def cancel_alarm(alarm_id: UUID):
    if alarm_id not in alarms_store:
        raise HTTPException(status_code=404, detail="Alarm not found")

    alarm = alarms_store[alarm_id]
    if alarm["status"] != "running":
        raise HTTPException(status_code=400, detail="Alarm is not running")

    alarm["status"] = "cancelled"
    return {"message": "Alarm cancelled", "alarm": alarm}
