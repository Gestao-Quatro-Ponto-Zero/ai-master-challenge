import { writable } from 'svelte/store';
import { browser } from '$app/environment';

export type Role = 'manager' | 'seller';

const getInitialRole = (): Role => {
	if (!browser) return 'seller';
	const stored = localStorage.getItem('g4_compass_role');
	return stored === 'manager' ? 'manager' : 'seller';
};

export const role = writable<Role>(getInitialRole());

if (browser) {
	role.subscribe((value) => {
		localStorage.setItem('g4_compass_role', value);
	});
}
