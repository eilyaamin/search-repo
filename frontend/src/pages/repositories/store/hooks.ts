import { StoreRepository } from './StoreRepository'

const repositoryStore = new StoreRepository()

export function useRepositoryStore() {
  return repositoryStore
}
