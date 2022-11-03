#include <assert.h>
#include <signal.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/time.h>

#include "private.h"
#include "uthread.h"
#include "queue.h"

#define STACK_SIZE 32768



struct uthread_tcb {
    /* TODO Phase 2 */

    /// each thread has own stack
    void* stack;
    /// to represent the state they are in: running, ready, or exited
    char* state[1];

    /// context of thread
    uthread_ctx_t *uctx;

};

struct uthread_tcb* currentThread;



/// we will have a global queue
queue_t q;

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

    /// store dequeued Item
    struct uthread_tcb* dequeuedItem;

    /// now dequeu
    queue_dequeue(q, (void **)&dequeuedItem);


    /// now the current thread will beccome the dequeued Item since that is where we are
    /// switching
    currentThread = dequeuedItem;

    /// add the current thread to the queue
    queue_enqueue(q, currentThreadSaved);




    /// now switch from the previus current to the dequeued Item which is where we go next

    uthread_ctx_switch(currentThreadSaved->uctx, dequeuedItem->uctx);





}

void uthread_exit(void)
{

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

    ///2. initialize its state to ready
    newThread->state[0] = "ready";

    ///allocate a new context object
    newThread->uctx = (uthread_ctx_t*)malloc(sizeof(uthread_ctx_t));

    ///initialize stack
    initializeStack(newThread);

    ///Initialize a thread's execution context
    uthread_ctx_init(newThread->uctx, newThread->stack, func, arg);

    /// add the TCB(object) of thread into the queue
    queue_enqueue(q, newThread);



    return 0;


}

int uthread_run(bool preempt, uthread_func_t func, void *arg)
{
    /* TODO Phase 2 */

    if (preempt)
	{
		int i = 0;
		i = i + 1;
	}


    q = queue_create();
    struct uthread_tcb *mainThread = (struct uthread_tcb*)malloc(sizeof(struct uthread_tcb));

    mainThread->uctx = (uthread_ctx_t *)malloc(sizeof(uthread_ctx_t));


    /// we set the main thread as the currentThread
    currentThread = mainThread;

    /// main thread creates a new thread
    uthread_create(func, arg);



    /// inside the loop of the main thread(this one) you
    /// yield until there are no more threads to schedule
    while(queue_length(q) != -1){
        uthread_yield();

    }

    return 0;















}

//void uthread_block(void)
//{
    /* TODO Phase 4 */
//}

//void uthread_unblock(struct uthread_tcb *uthread)
//{
    /* TODO Phase 4 */
//}



