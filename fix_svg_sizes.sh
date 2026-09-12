#!/bin/bash
sed -i 's/size="55" style="width: 100%; height: 100%;"/size="55"/g' frontend/src/views/ListView.vue
sed -i 's/size="55" style="width: 100%; height: 100%;"/size="55"/g' frontend/src/components/AddItemModal.vue
sed -i 's/size="55" style="width: 100%; height: 100%; opacity: 0.5;"/size="55" style="opacity: 0.5;"/g' frontend/src/views/ListView.vue
sed -i 's/class="w-16 h-16 mb-2 rounded-xl bg-slate-700\/50 flex items-center justify-center p-2"/class="w-[55px] h-[55px] mb-2 rounded-xl bg-slate-700\/50 flex items-center justify-center p-0"/g' frontend/src/views/ListView.vue
sed -i 's/class="w-16 h-16 mb-2 rounded-xl bg-slate-700\/50 flex items-center justify-center p-2"/class="w-[55px] h-[55px] mb-2 rounded-xl bg-slate-700\/50 flex items-center justify-center p-0"/g' frontend/src/components/AddItemModal.vue
sed -i 's/style="width: 64px; height: 64px;/style="width: 55px; height: 55px;/g' frontend/src/views/ListView.vue
