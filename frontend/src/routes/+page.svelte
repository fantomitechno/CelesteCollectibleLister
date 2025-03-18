<script lang="ts">
	import { Download } from '$lib/wailsjs/go/main/App.js';

	let modURL = '';

	let modName = '';
	let err = null;

	let download = () => {
		Download(modURL)
			.then((r) => (modName = r))
			.catch((err) => (err = err));
	};

	let cancel = () => {
		modName = '';
	};
</script>

<main>
	<section>
		<hgroup id="titles">
			<h1>Celeste Modded Map Collectible Lister</h1>
		</hgroup>
		<span>
			{#if modName == ''}
				<form on:submit={download}>
					<label>
						URL
						<input name="url" type="text" required bind:value={modURL} />
					</label>
					<button>Submit</button>
				</form>
			{:else}
				{modName}
				<button on:click={cancel}>Cancel</button>
			{/if}
		</span>
	</section>
</main>

<style>
	span {
		margin: 1em 0.5em;
		display: flex;
		flex-direction: column;

		width: 80%;
		align-self: center;
		border: 0.2em solid var(--color-primary);
		border-radius: 1em;
		padding: 1em;
		background-color: var(--color-bg-0);
		width: calc(100% - 2.4em);
	}

	label {
		margin: 0.5em 0;
	}

	button {
		width: fit-content;
		padding: 0.2em 0.5em;
		margin: 1em 0 0;
		border: 0.1em solid var(--color-secondary);
		border-radius: 0.5em;
	}

	input[type='text'] {
		width: 98.2%;
		font: inherit;
		padding: 0.2em 0.5em;
		background-color: var(--color-bg-1);
		border: 0.1em solid var(--color-secondary);
		border-radius: 0.5em;
	}
</style>
