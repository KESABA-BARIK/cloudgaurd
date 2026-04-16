from bson import ObjectId

def serialize(data):
    if isinstance(data, list):
        return [serialize(x) for x in data]
    if isinstance(data, dict):
        return {k: serialize(v) for k, v in data.items() if k != "_id"}
    if isinstance(data, ObjectId):
        return str(data)
    return data