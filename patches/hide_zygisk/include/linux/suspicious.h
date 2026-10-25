#ifndef _LINUX_SUSPICIOUS_H_
#define _LINUX_SUSPICIOUS_H_

#include <linux/fs.h>
#include <linux/mount.h>

#define getname_safe(name) (name == NULL ? ERR_PTR(-EINVAL) : getname(name))
#define putname_safe(name) (IS_ERR(name) ? NULL : putname(name))

int is_suspicious_path(const struct path* const file);
int is_suspicious_mount(struct vfsmount* const mnt, const struct path* const root);
int suspicious_path(const struct filename* const name);
bool suspicious_pid_alive(int pid);
bool suspicious_modules_list(void);

#endif /* _LINUX_SUSPICIOUS_H_ */
