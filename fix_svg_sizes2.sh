#!/bin/bash
sed -i 's/w-16 h-16/w-\[55px\] h-\[55px\] p-0/g' frontend/src/views/ListView.vue
sed -i 's/p-2//g' frontend/src/views/ListView.vue
sed -i 's/class="w-\[55px\] h-\[55px\] mb-2 rounded-xl flex items-center justify-center p-0"/class="w-[55px] h-[55px] mb-2 rounded-xl bg-slate-700\/50 flex items-center justify-center p-0"/g' frontend/src/views/ListView.vue

# for completed item:
sed -i 's/class="w-\[55px\] h-\[55px\] p-0 mb-2 rounded-xl flex items-center justify-center "/class="w-[55px] h-[55px] mb-2 rounded-xl flex items-center justify-center"/g' frontend/src/views/ListView.vue
