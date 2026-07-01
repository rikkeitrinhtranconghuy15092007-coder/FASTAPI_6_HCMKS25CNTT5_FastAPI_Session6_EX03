from fastapi import FastAPI, HTTPException, Path, Query, status
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

app = FastAPI()

class RoomStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    IN_USE = "IN_USE"
    MAINTENANCE = "MAINTENANCE"

class SlotEnum(str, Enum):
    MORNING = "MORNING"
    AFTERNOON = "AFTERNOON"
    EVENING = "EVENING"

class RoomCreateUpdate(BaseModel):
    code: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    capacity: int = Field(..., gt=0)
    status: RoomStatus

class BookingCreate(BaseModel):
    room_id: int
    class_name: str = Field(..., min_length=1)
    student_count: int = Field(..., gt=0)
    date: str = Field(..., min_length=1)
    slot: SlotEnum

rooms = [
    {"id": 1, "code": "R101", "name": "Room 101", "capacity": 30, "status": "AVAILABLE"},
    {"id": 2, "code": "R102", "name": "Room 102", "capacity": 20, "status": "AVAILABLE"},
    {"id": 3, "code": "R103", "name": "Room 103", "capacity": 40, "status": "MAINTENANCE"}
]

room_bookings = [
    {
        "id": 1,
        "room_id": 1,
        "class_name": "Python Basic",
        "student_count": 25,
        "date": "2026-07-01",
        "slot": "MORNING"
    }
]

@app.get("/rooms")
def get_rooms(
    keyword: Optional[str] = Query(None),
    status: Optional[RoomStatus] = Query(None),
    min_capacity: Optional[int] = Query(None)
):
    result = rooms.copy()
    
    if keyword:
        kw_lower = keyword.lower()
        result = [
            r for r in result 
            if kw_lower in r["code"].lower() or kw_lower in r["name"].lower()
        ]
        
    if status:
        result = [r for r in result if r["status"] == status]
        
    if min_capacity is not None:
        result = [r for r in result if r["capacity"] >= min_capacity]
        
    return result

@app.get("/rooms/{room_id}")
def get_room_detail(room_id: int = Path(...)):
    for r in rooms:
        if r["id"] == room_id:
            return r
    raise HTTPException(status_code=404, detail="Room not found")

@app.post("/rooms", status_code=status.HTTP_201_CREATED)
def create_room(room_in: RoomCreateUpdate):
    for r in rooms:
        if r["code"] == room_in.code:
            raise HTTPException(status_code=400, detail="Mã phòng học đã tồn tại")
            
    new_id = max(r["id"] for r in rooms) + 1 if rooms else 1
    new_room = {
        "id": new_id,
        "code": room_in.code,
        "name": room_in.name,
        "capacity": room_in.capacity,
        "status": room_in.status.value
    }
    rooms.append(new_room)
    return {"message": "Thêm phòng học thành công", "room": new_room}

@app.put("/rooms/{room_id}")
def update_room(room_in: RoomCreateUpdate, room_id: int = Path(...)):
    target_room = None
    for r in rooms:
        if r["id"] == room_id:
            target_room = r
            break
            
    if not target_room:
        raise HTTPException(status_code=404, detail="Room not found")
        
    for r in rooms:
        if r["code"] == room_in.code and r["id"] != room_id:
            raise HTTPException(status_code=400, detail="Mã phòng học đã bị trùng")
            
    target_room["code"] = room_in.code
    target_room["name"] = room_in.name
    target_room["capacity"] = room_in.capacity
    target_room["status"] = room_in.status.value
    
    return {"message": "Cập nhật phòng học thành công", "room": target_room}

@app.delete("/rooms/{room_id}")
def delete_room(room_id: int = Path(...)):
    for index, r in enumerate(rooms):
        if r["id"] == room_id:
            rooms.pop(index)
            return {"message": "Xóa phòng học thành công"}
    raise HTTPException(status_code=404, detail="Room not found")

@app.get("/room-bookings")
def get_bookings():
    return room_bookings

@app.post("/room-bookings", status_code=status.HTTP_201_CREATED)
def create_booking(booking_in: BookingCreate):
    target_room = None
    for r in rooms:
        if r["id"] == booking_in.room_id:
            target_room = r
            break
            
    if not target_room:
        raise HTTPException(status_code=400, detail="Phòng học không tồn tại")
        
    if target_room["status"] != "AVAILABLE":
        raise HTTPException(status_code=400, detail="Phòng đang không ở trạng thái sẵn sàng (AVAILABLE)")
        
    if booking_in.student_count > target_room["capacity"]:
        raise HTTPException(status_code=400, detail="Số lượng học viên vượt quá sức chứa của phòng")
        
    for b in room_bookings:
        if b["room_id"] == booking_in.room_id and b["date"] == booking_in.date and b["slot"] == booking_in.slot.value:
            raise HTTPException(status_code=400, detail="Phòng này đã có lịch đặt vào ngày và ca học này")
            
    new_id = max(b["id"] for b in room_bookings) + 1 if room_bookings else 1
    new_booking = {
        "id": new_id,
        "room_id": booking_in.room_id,
        "class_name": booking_in.class_name,
        "student_count": booking_in.student_count,
        "date": booking_in.date,
        "slot": booking_in.slot.value
    }
    room_bookings.append(new_booking)
    return {"message": "Đặt lịch sử dụng phòng thành công", "booking": new_booking}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)