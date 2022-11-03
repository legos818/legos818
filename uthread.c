#include <assert.h>
#include <signal.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/time.h>
#include <string.h>

#include "private.h"
#include "uthread.h"
#include "queue.h"


/// in order to get the current thread
struct uthread_tcb* currentThread;

/// we will have a global queue
queue_t q;



struct uthread_tcb {
    /* TODO Phase 2 */

    /// each thread has own stack
    void* stack;
    /// to represent the state they are in: running, ready,blocked or exited
    char* state[1];

    /// context of thread
    uthread_ctx_t *uctx;

};


void initializeStack(struct uthread_tcb* thread){
    thread->stack = uthread_ctx_alloc_stack();

}



struct uthread_tcb *uthread_current(void)
{
    /* TODO Phase 2/4 */

    return currentThread;
}

void uthread_yield(void)
{
    /* TODO Phase 2 */



    /// we need to store the current running thread so we can context switch
    struct uthread_tcb* currentThreadSaved = uthread_current();

    /// we want to change the state of previous current Thread
    /// if it is in a running state then
    /// change it from running to ready so we can add to queue
    /// it is necessary because it causes problems when program
    /// calls uthread_exit, specially for sem_simple.c
    if(strcmp(currentThreadSaved->state[0], "running") == 0){
        currentThreadSaved->state[0] = "ready";
    }

    /// store dequeued Item
    struct uthread_tcb* dequeuedItem;

    /// now dequeu
    queue_dequeue(q, (void **)&dequeuedItem);

    /// now the current thread will become the dequeued Item since that is where we are
    /// switching
    currentThread = dequeuedItem;

    /// it was in a ready state now we set the state to running
    dequeuedItem->state[0] = "running";


    /// add the previous current thread to the queue
    /// only if it is ready will it be added to the queue
    /// also takes care of the case if the thread exits we dont want to
    /// add it to the ready queue
    if(strcmp(currentThreadSaved->state[0], "ready") == 0){
        queue_enqueue(q, currentThreadSaved);
    }

    /// now switch from the previous current to the dequeued Item which is where we go next
    uthread_ctx_switch(currentThreadSaved->uctx, dequeuedItem->uctx);






}

void uthread_exit(void)
{
    /* TODO Phase 2 */

    /// get the current running thread
    struct uthread_tcb* currentSavedThread = uthread_current();
    ///exit from the currently running thread by setting its state to exited
    currentSavedThread->state[0] = "exited";


    /// now we go to the next available thread in the ready queue
    ///and we dont add this to the queue since we just set the state to exited
    uthread_yield();


}

int uthread_create(uthread_func_t func, void *arg)
{
    /* TODO Phase 2 */

    /// 1. create an object thread
    struct uthread_tcb *newThread = (struct uthread_tcb*)malloc(sizeof(struct uthread_tcb));

    /// check case of failure in memory allocation
    if(newThread == NULL){
        return -1;
    }

    ///2. initialize its state to ready
    newThread->state[0] = "ready";

    ///allocate a new context object
    newThread->uctx = (uthread_ctx_t*)malloc(sizeof(uthread_ctx_t));

    /// check for failure in allocation of context
    if(newThread->uctx == NULL){
        return -1;
    }

    ///initialize stack
    initializeStack(newThread);

    ///Initialize a thread's execution context
    int returnValue = uthread_ctx_init(newThread->uctx, newThread->stack, func, arg);
    /// so if function failed to initialize threads execution context
    if(returnValue == -1){
        return -1;
    }

    /// add the TCB(object) of thread into the ready queue
    queue_enqueue(q, newThread);



    return 0;


}

int uthread_run(bool preempt, uthread_func_t func, void *arg)
{
    /* TODO Phase 2 */



    /// create the ready queue that will be used
    q = queue_create();
    /// create the main thread
    struct uthread_tcb *mainThread = (struct uthread_tcb*)malloc(sizeof(struct uthread_tcb));

    /// return -1 in case of failure

    /// if failure in memory allocation
    if(mainThread == NULL){
        return -1;
    }

    mainThread->uctx = (uthread_ctx_t *)malloc(sizeof(uthread_ctx_t));
    /// if failure in context creation
    if(mainThread->uctx == NULL){
        return -1;
    }


    /// we set the main thread as the currentThread
    currentThread = mainThread;

    /// main thread creates a new thread
    uthread_create(func, arg);



    /// inside the loop of the main thread(this one) you
    /// yield until there are no more threads to schedule so we when length is 0
    while(queue_length(q) != 0){
        uthread_yield();
    }

    return 0;















}

void uthread_block(void)
{
    /* TODO Phase 4 */

    /// 1. get the current thread
    struct uthread_tcb* currentSavedThread = uthread_current();

    ///2. set its state to blocked
    currentSavedThread->state[0] = "blocked";

    /// this thread should not run until its put back to ready
    /// queue

    ///3. go to the next available thread
    uthread_yield();


}

void uthread_unblock(struct uthread_tcb *uthread)
{
    /* TODO Phase 4 */


    /// unblock and set it to ready
    /// we can assume it is in blocked state so we just change it to ready
    uthread->state[0] = "ready";

    //// since it is ready then add to queue of ready threads
    queue_enqueue(q, uthread);






}


