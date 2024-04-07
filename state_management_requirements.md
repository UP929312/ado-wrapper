# State Managed Resources

To be viable as a state managed resources, a class must define the following attributes:

- from_request_payload(data: dict)
- get_by_id(resouce_id: str)
- create() (can just raise NotImplementedError)
- update(attribute_name, attribute_value) (can just raise NotImplementedError)
- delete_by_id(resource_id: str)
