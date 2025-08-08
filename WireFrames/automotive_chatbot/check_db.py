import sys
sys.path.append('backend')
from config.database import get_collection

collection = get_collection('conversations')
docs = list(collection.find({}))
print(f'Current records: {len(docs)}')
for doc in docs:
    print(f'ID: {doc.get("_id")}')
    print(f'ConvID: {doc.get("conversation_id")}')
    print(f'Content: {doc.get("content", "")}')
    print('---')