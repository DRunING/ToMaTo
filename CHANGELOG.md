# Changelog

This file should be used to track all changes to ToMaTo in a similar way to [VpnCloud](https://github.com/dswd/vpncloud.rs/blob/master/CHANGELOG.md)
Entries should be prefixed with some tags:
- Status tags: `added`, `fixed`, `changed`, `removed`
- Component tags: `backend`, `web`, `cli`, `hostmanager`
Entries should be sorted by component and status with important entries and entries with multiple components being on top.


### UNRELEASED
- [backend, changed] Using __slots__ for generic classes, attributes and schemas and tasks to save space and increase performance
- [backend, fixed] Fixed problem with dumping stack variables when dumping errors
- [backend, fixed] Fixed problem with non-existing error groups
- [backend, fixed] Fixed problem with accounting aggregation for topologies, users and organizations
- [backend, fixed] Gracefully handling errors on topology timeout
- [backend, fixed] Gracefully handling errors on host component synchronization
- [backend, fixed] Fixed profiling when server does not terminate
- [backend, removed] Removed useless dump environment infos