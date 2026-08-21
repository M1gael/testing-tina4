/* Run CLOCK_REALTIME fast and leave CLOCK_MONOTONIC alone.
 *
 * This is the whole point of the proof: the framework times the bound on
 * CLOCK_MONOTONIC (time.monotonic) and libpq times its own connect_timeout on
 * CLOCK_REALTIME (gettimeofday). NTP moves realtime -- it slews it continuously
 * and steps it outright -- and never touches monotonic. This shim makes that
 * divergence happen on demand instead of waiting for a runner to have a bad day.
 *
 *   SKEW_RATE   realtime advances this much faster than monotonic (default 1.0)
 *   SKEW_LOG    if set, append the MONOTONIC timestamp of every gettimeofday
 *               call to this file. Python reads the clock through
 *               clock_gettime, so gettimeofday calls are libpq's alone -- which
 *               is how the exposure window gets measured.
 *
 * Build:  gcc -shared -fPIC -O2 -o skew.so skew.c -ldl
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/time.h>
#include <time.h>
#include <unistd.h>

static int (*real_gettimeofday)(struct timeval *, void *);
static int (*real_clock_gettime)(clockid_t, struct timespec *);
static time_t (*real_time)(time_t *);

static double rate = 1.0;
static long long base_ns = 0;
static int log_fd = -1;
static int ready = 0;

static long long raw_real_ns(void)
{
    struct timespec ts;
    real_clock_gettime(CLOCK_REALTIME, &ts);
    return (long long) ts.tv_sec * 1000000000LL + ts.tv_nsec;
}

static void init(void)
{
    if (ready) return;
    real_gettimeofday = dlsym(RTLD_NEXT, "gettimeofday");
    real_clock_gettime = dlsym(RTLD_NEXT, "clock_gettime");
    real_time = dlsym(RTLD_NEXT, "time");
    const char *r = getenv("SKEW_RATE");
    if (r) rate = atof(r);
    const char *lg = getenv("SKEW_LOG");
    if (lg) log_fd = open(lg, O_WRONLY | O_CREAT | O_TRUNC, 0644);
    base_ns = raw_real_ns();
    ready = 1;
}

/* how far ahead of the true clock our faked realtime has drifted by now */
static long long offset_ns(void)
{
    if (rate == 1.0) return 0;
    return (long long) ((double) (raw_real_ns() - base_ns) * (rate - 1.0));
}

int gettimeofday(struct timeval *tv, void *tz)
{
    init();
    int r = real_gettimeofday(tv, tz);
    if (log_fd >= 0) {
        struct timespec m;
        real_clock_gettime(CLOCK_MONOTONIC, &m);
        char buf[64];
        int n = snprintf(buf, sizeof buf, "%lld\n",
                         (long long) m.tv_sec * 1000000000LL + m.tv_nsec);
        if (n > 0) { ssize_t w = write(log_fd, buf, (size_t) n); (void) w; }
    }
    if (r == 0 && tv) {
        long long ns = offset_ns();
        tv->tv_sec += ns / 1000000000LL;
        tv->tv_usec += (ns % 1000000000LL) / 1000;
        if (tv->tv_usec >= 1000000) { tv->tv_sec++; tv->tv_usec -= 1000000; }
    }
    return r;
}

int clock_gettime(clockid_t id, struct timespec *ts)
{
    init();
    int r = real_clock_gettime(id, ts);
    if (r == 0 && ts && id == CLOCK_REALTIME) {
        long long ns = offset_ns();
        ts->tv_sec += ns / 1000000000LL;
        ts->tv_nsec += ns % 1000000000LL;
        if (ts->tv_nsec >= 1000000000LL) { ts->tv_sec++; ts->tv_nsec -= 1000000000LL; }
    }
    return r;
}

time_t time(time_t *t)
{
    init();
    time_t v = real_time(NULL) + (time_t) (offset_ns() / 1000000000LL);
    if (t) *t = v;
    return v;
}
